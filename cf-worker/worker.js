// PromptDock Cloudflare Worker Backend
// 纯原生 Web Crypto API 实现，无需任何 npm 依赖
// 集成边缘防刷、IP 频率限制、输入格式深度白名单与防暴力破解

const JWT_SECRET = "PROMPTDOCK_SECRET_KEY_CHANGE_IF_NEEDED";

// 辅助函数：跨域响应头
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function errorResponse(message, status = 400) {
  return jsonResponse({ error: message }, status);
}

function rateLimitResponse(message, retryAfter = 60) {
  return new Response(JSON.stringify({ error: message }), {
    status: 429,
    headers: {
      ...corsHeaders,
      "Content-Type": "application/json",
      "Retry-After": String(retryAfter),
    },
  });
}

// -------------------------------------------------------------
// 边缘防护与限流模块 (Edge In-Memory Rate Limiting)
// 在命中 D1 数据库前直接阻断恶意流量，保护免费额度
// -------------------------------------------------------------

const rateLimitMap = new Map();
const failedLoginMap = new Map();

function getClientIP(request) {
  return (
    request.headers.get("cf-connecting-ip") ||
    request.headers.get("x-real-ip") ||
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    "unknown"
  );
}

function checkRateLimit(key, maxRequests, windowMs) {
  const now = Date.now();
  if (rateLimitMap.size > 2000) {
    for (const [k, record] of rateLimitMap.entries()) {
      if (record.resetTime <= now) rateLimitMap.delete(k);
    }
  }

  const record = rateLimitMap.get(key);
  if (!record || record.resetTime <= now) {
    rateLimitMap.set(key, { count: 1, resetTime: now + windowMs });
    return { allowed: true, remaining: maxRequests - 1 };
  }

  if (record.count >= maxRequests) {
    const retryAfter = Math.ceil((record.resetTime - now) / 1000);
    return { allowed: false, retryAfter };
  }

  record.count += 1;
  return { allowed: true, remaining: maxRequests - record.count };
}

// 标准电子邮箱正则
const EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$/;

function isValidEmail(email) {
  if (!email || typeof email !== "string") return false;
  if (email.length < 5 || email.length > 80) return false;
  return EMAIL_REGEX.test(email);
}

// -------------------------------------------------------------
// 加密与 Token 工具（Web Crypto API）
// -------------------------------------------------------------

async function sha256(str) {
  const buf = new TextEncoder().encode(str);
  const hash = await crypto.subtle.digest("SHA-256", buf);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function generateSalt() {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function hashPassword(password, salt) {
  return await sha256(password + ":" + salt + ":" + JWT_SECRET);
}

function base64UrlEncode(str) {
  return btoa(str).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64UrlDecode(str) {
  str = str.replace(/-/g, "+").replace(/_/g, "/");
  while (str.length % 4) str += "=";
  return atob(str);
}

async function createJWT(payload) {
  const header = { alg: "HS256", typ: "JWT" };
  const exp = Math.floor(Date.now() / 1000) + 365 * 24 * 60 * 60; // 1 年有效期
  const fullPayload = { ...payload, exp };

  const encodedHeader = base64UrlEncode(JSON.stringify(header));
  const encodedPayload = base64UrlEncode(JSON.stringify(fullPayload));
  const data = `${encodedHeader}.${encodedPayload}`;

  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(JWT_SECRET),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(data)
  );
  const encodedSignature = base64UrlEncode(
    String.fromCharCode(...new Uint8Array(signature))
  );

  return `${data}.${encodedSignature}`;
}

async function verifyJWT(token) {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const [encodedHeader, encodedPayload, encodedSignature] = parts;
    const data = `${encodedHeader}.${encodedPayload}`;

    const key = await crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(JWT_SECRET),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["verify"]
    );

    const signature = Uint8Array.from(base64UrlDecode(encodedSignature), (c) =>
      c.charCodeAt(0)
    );
    const valid = await crypto.subtle.verify(
      "HMAC",
      key,
      signature,
      new TextEncoder().encode(data)
    );
    if (!valid) return null;

    const payload = JSON.parse(base64UrlDecode(encodedPayload));
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
      return null;
    }
    return payload;
  } catch (e) {
    return null;
  }
}

async function getAuthUser(request) {
  const auth = request.headers.get("Authorization");
  if (!auth || !auth.startsWith("Bearer ")) return null;
  const token = auth.substring(7).trim();
  return await verifyJWT(token);
}

// -------------------------------------------------------------
// 主处理入口
// -------------------------------------------------------------

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    const db = env.DB;
    if (!db && url.pathname.startsWith("/api/")) {
      return errorResponse("D1 数据库绑定未检测到，请检查 wrangler.toml 中的 binding 是否为 DB", 500);
    }

    // --- 认证接口: 注册 ---
    if (url.pathname === "/api/register" && request.method === "POST") {
      const ip = getClientIP(request);

      // 防护 1：IP 频次限制（10 分钟内同一个 IP 最多注册 3 次，防止脚本批量刷库）
      const ipLimit = checkRateLimit(`reg:${ip}`, 3, 10 * 60 * 1000);
      if (!ipLimit.allowed) {
        return rateLimitResponse(
          `注册请求过于频繁，请等待 ${ipLimit.retryAfter} 秒后再试`,
          ipLimit.retryAfter
        );
      }

      // 防护 2：系统注册开关（可通过 Cloudflare 变量随时一键暂停注册）
      if (env.REGISTRATION_DISABLED === "true") {
        return errorResponse("管理员已暂时关闭新用户注册", 403);
      }

      try {
        const body = await request.json();
        const { email, password, nickname, avatar, invite_code, honeypot } = body;

        // 防护 3：机器人蜜罐拦截（自动化爬虫脚本若盲目填充隐藏字段则直接拒绝）
        if (honeypot) {
          return errorResponse("请求异常", 400);
        }

        // 防护 4：私有邀请码机制（若服务端配置了 INVITE_CODE，则开启私有部署邀请保护）
        if (env.INVITE_CODE && env.INVITE_CODE.trim() !== "") {
          if (!invite_code || invite_code.trim() !== env.INVITE_CODE.trim()) {
            return errorResponse("此节点已开启邀请注册模式，请输入有效邀请码", 403);
          }
        }

        // 防护 5：严格邮箱格式校验（长度与正则）
        if (!isValidEmail(email)) {
          return errorResponse("请输入规范有效的电子邮箱地址 (如 name@example.com)");
        }

        // 防护 6：密码长度防护（防过短及巨型字符串 CPU 耗尽 DoS）
        if (!password || typeof password !== "string" || password.length < 6) {
          return errorResponse("密码长度不能少于 6 位");
        }
        if (password.length > 64) {
          return errorResponse("密码长度不能超过 64 位");
        }

        // 防护 7：昵称与头像体积校验（防止超大 Base64 塞满 D1 存储）
        const cleanNickname = typeof nickname === "string" ? nickname.trim().slice(0, 32) : "";
        let cleanAvatar = "";
        if (avatar) {
          if (typeof avatar !== "string" || avatar.length > 120000) {
            return errorResponse("头像文件过大，请选择不超过 100KB 的图片");
          }
          cleanAvatar = avatar;
        }

        const cleanEmail = email.trim().toLowerCase();

        // 仅在前置安全检查全部通过后，才查询 D1 数据库
        const existing = await db
          .prepare("SELECT id FROM users WHERE email = ?")
          .bind(cleanEmail)
          .first();
        if (existing) {
          return errorResponse("该邮箱已被注册，请直接登录");
        }

        const id = crypto.randomUUID();
        const salt = generateSalt();
        const passwordHash = await hashPassword(password, salt);
        const now = Date.now();

        await db
          .prepare(
            "INSERT INTO users (id, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)"
          )
          .bind(id, cleanEmail, passwordHash, salt, now)
          .run();

        if (cleanNickname || cleanAvatar) {
          const initialSettings = JSON.stringify({
            cloud_nickname: cleanNickname,
            cloud_avatar: cleanAvatar,
            folders: [],
            collapsed_groups: [],
            edge_dock: true
          });
          await db
            .prepare(
              "INSERT INTO user_settings (user_id, data, updated_at) VALUES (?, ?, ?)"
            )
            .bind(id, initialSettings, now)
            .run();
        }

        const token = await createJWT({ uid: id, email: cleanEmail });
        return jsonResponse({
          token,
          email: cleanEmail,
          nickname: cleanNickname,
          avatar: cleanAvatar,
          message: "注册成功"
        });
      } catch (err) {
        return errorResponse("注册失败: " + err.message, 500);
      }
    }

    // --- 认证接口: 登录 ---
    if (url.pathname === "/api/login" && request.method === "POST") {
      const ip = getClientIP(request);

      // 防护 1：IP 登录频次限制（1 分钟内同一个 IP 最多尝试 15 次）
      const ipLimit = checkRateLimit(`login:${ip}`, 15, 60 * 1000);
      if (!ipLimit.allowed) {
        return rateLimitResponse(
          `登录尝试过于频繁，请等待 ${ipLimit.retryAfter} 秒后再试`,
          ipLimit.retryAfter
        );
      }

      try {
        const { email, password } = await request.json();
        if (!email || !password || typeof password !== "string") {
          return errorResponse("请输入邮箱和密码");
        }
        const cleanEmail = email.trim().toLowerCase();

        // 防护 2：单账号防暴力破解（连续输错 5 次密码锁定 5 分钟）
        const failedRecord = failedLoginMap.get(cleanEmail);
        const now = Date.now();
        if (failedRecord && failedRecord.lockedUntil > now) {
          const waitSec = Math.ceil((failedRecord.lockedUntil - now) / 1000);
          return rateLimitResponse(
            `该账号连续登录失败过多，已被安全锁定，请于 ${waitSec} 秒后再试`,
            waitSec
          );
        }

        const user = await db
          .prepare("SELECT id, email, password_hash, salt FROM users WHERE email = ?")
          .bind(cleanEmail)
          .first();
        if (!user) {
          return errorResponse("邮箱或密码错误", 401);
        }
        const passwordHash = await hashPassword(password, user.salt);
        if (passwordHash !== user.password_hash) {
          const cur = failedLoginMap.get(cleanEmail) || { count: 0, lockedUntil: 0 };
          cur.count += 1;
          if (cur.count >= 5) {
            cur.lockedUntil = now + 5 * 60 * 1000;
          }
          failedLoginMap.set(cleanEmail, cur);
          return errorResponse("邮箱或密码错误", 401);
        }

        // 登录成功，清除该账号的历史失败计数
        failedLoginMap.delete(cleanEmail);

        let nickname = "";
        let avatar = "";
        const settingsRow = await db
          .prepare("SELECT data FROM user_settings WHERE user_id = ?")
          .bind(user.id)
          .first();
        if (settingsRow && settingsRow.data) {
          try {
            const parsed = JSON.parse(settingsRow.data);
            nickname = parsed.cloud_nickname || "";
            avatar = parsed.cloud_avatar || "";
          } catch (e) {}
        }

        const token = await createJWT({ uid: user.id, email: user.email });
        return jsonResponse({
          token,
          email: user.email,
          nickname,
          avatar,
          message: "登录成功"
        });
      } catch (err) {
        return errorResponse("登录失败: " + err.message, 500);
      }
    }

    if (url.pathname === "/api/me" && request.method === "GET") {
      const user = await getAuthUser(request);
      if (!user) return errorResponse("未授权或登录已过期", 401);
      return jsonResponse({ user });
    }

    // --- 数据同步接口 ---
    if (url.pathname === "/api/sync/pull" && request.method === "GET") {
      const user = await getAuthUser(request);
      if (!user) return errorResponse("未授权", 401);

      const since = parseInt(url.searchParams.get("since") || "0", 10);
      try {
        const promptsRes = await db
          .prepare(
            "SELECT id, title, folder, pinned, color, segments, updated_at, is_deleted FROM prompts WHERE user_id = ? AND updated_at > ? ORDER BY updated_at ASC"
          )
          .bind(user.uid, since)
          .all();

        const prompts = (promptsRes.results || []).map((p) => ({
          ...p,
          pinned: Boolean(p.pinned),
          is_deleted: Boolean(p.is_deleted),
          segments: typeof p.segments === "string" ? JSON.parse(p.segments) : p.segments,
        }));

        const settingsRow = await db
          .prepare("SELECT data, updated_at FROM user_settings WHERE user_id = ?")
          .bind(user.uid)
          .first();

        let settings = null;
        if (settingsRow && settingsRow.updated_at > since) {
          try {
            settings = JSON.parse(settingsRow.data);
          } catch (_) {}
        }

        return jsonResponse({
          prompts,
          settings,
          server_time: Date.now(),
        });
      } catch (err) {
        return errorResponse("拉取失败: " + err.message, 500);
      }
    }

    if (url.pathname === "/api/sync/push" && request.method === "POST") {
      const user = await getAuthUser(request);
      if (!user) return errorResponse("未授权", 401);

      try {
        const body = await request.json();
        const { prompts = [], settings = null, timestamp = Date.now() } = body;

        // 安全限制：防止单次提交海量条目耗尽 D1 batch 限额
        if (!Array.isArray(prompts) || prompts.length > 500) {
          return errorResponse("单次同步卡片数量不能超过 500 条");
        }

        const stmts = [];
        for (const p of prompts) {
          const segJson = JSON.stringify(p.segments || []);
          const isDel = p.is_deleted ? 1 : 0;
          const pinVal = p.pinned ? 1 : 0;
          const updated = p.updated_at || timestamp;

          stmts.push(
            db
              .prepare(
                `INSERT INTO prompts (id, user_id, title, folder, pinned, color, segments, updated_at, is_deleted)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                 ON CONFLICT(id) DO UPDATE SET
                   title = excluded.title,
                   folder = excluded.folder,
                   pinned = excluded.pinned,
                   color = excluded.color,
                   segments = excluded.segments,
                   updated_at = excluded.updated_at,
                   is_deleted = excluded.is_deleted
                 WHERE excluded.updated_at >= prompts.updated_at`
              )
              .bind(
                p.id,
                user.uid,
                p.title || "",
                p.folder || "",
                pinVal,
                p.color || "#f5f6fa",
                segJson,
                updated,
                isDel
              )
          );
        }

        if (settings) {
          // 限制自定义配置体积，防止超大头像注入
          const settingsStr = JSON.stringify(settings);
          if (settingsStr.length > 250000) {
            return errorResponse("个性化设置配置体积过大");
          }

          stmts.push(
            db
              .prepare(
                `INSERT INTO user_settings (user_id, data, updated_at)
                 VALUES (?, ?, ?)
                 ON CONFLICT(user_id) DO UPDATE SET
                   data = excluded.data,
                   updated_at = excluded.updated_at
                 WHERE excluded.updated_at >= user_settings.updated_at`
              )
              .bind(user.uid, settingsStr, timestamp)
          );
        }

        if (stmts.length > 0) {
          await db.batch(stmts);
        }

        return jsonResponse({ success: true, count: stmts.length, server_time: Date.now() });
      } catch (err) {
        return errorResponse("推送失败: " + err.message, 500);
      }
    }

    // --- 随身 Web 页面与静态资源 ---
    if (url.pathname === "/login") {
      const loginUrl = new URL(request.url);
      loginUrl.pathname = "/login.html";
      return env.ASSETS ? await env.ASSETS.fetch(new Request(loginUrl, request)) : new Response("Not found", { status: 404 });
    }

    if (env.ASSETS) {
      return await env.ASSETS.fetch(request);
    }

    return new Response(renderWebCompanion(), {
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  },
};

// -------------------------------------------------------------
// 嵌入式移动 / 桌面随身 Web 页面
// -------------------------------------------------------------
function renderWebCompanion() {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>PromptDock - 随身提示词卡</title>
  <style>
    :root {
      --bg: #f8f9fa;
      --card-bg: #ffffff;
      --primary: #4361ee;
      --primary-hover: #3751cc;
      --text: #2b2d42;
      --text-muted: #8d99ae;
      --border: #e2e8f0;
      --radius: 14px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif; -webkit-tap-highlight-color: transparent; }
    body { background-color: var(--bg); color: var(--text); padding-bottom: 60px; min-height: 100vh; }
    
    /* 顶部导航 */
    header {
      position: sticky; top: 0; z-index: 100;
      background: rgba(255, 255, 255, 0.92);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 12px 16px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .brand { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 17px; color: var(--primary); }
    .brand-logo { width: 28px; height: 28px; border-radius: 8px; background: var(--primary); display: flex; align-items: center; justify-content: center; color: white; font-size: 15px; font-weight: 800; }
    .user-info { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--text-muted); }
    .logout-btn { background: none; border: 1px solid var(--border); border-radius: 6px; padding: 4px 8px; font-size: 12px; color: var(--text-muted); cursor: pointer; }
    
    /* 搜索与分类 */
    .toolbar { padding: 12px 16px; display: flex; flex-direction: column; gap: 10px; max-width: 720px; margin: 0 auto; }
    .search-box {
      width: 100%; border: 1px solid var(--border); border-radius: 10px;
      padding: 10px 14px; font-size: 14px; background: white; outline: none;
    }
    .search-box:focus { border-color: var(--primary); }
    .folders-bar { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; scrollbar-width: none; }
    .folders-bar::-webkit-scrollbar { display: none; }
    .folder-pill {
      white-space: nowrap; font-size: 13px; padding: 6px 14px; border-radius: 20px;
      background: white; border: 1px solid var(--border); color: var(--text-muted); cursor: pointer;
    }
    .folder-pill.active { background: var(--primary); color: white; border-color: var(--primary); }
    
    /* 卡片列表 */
    .container { max-width: 720px; margin: 0 auto; padding: 0 16px; display: flex; flex-direction: column; gap: 14px; }
    .card {
      background: var(--card-bg); border-radius: var(--radius);
      padding: 16px; border: 1px solid var(--border);
      box-shadow: 0 2px 6px rgba(0,0,0,0.03); transition: transform 0.15s;
    }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .card-title { font-weight: 600; font-size: 15px; color: var(--text); }
    .badge-pin { font-size: 11px; color: var(--primary); background: #eef2ff; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
    
    .segment {
      background: #f8fafc; border: 1px dashed var(--border); border-radius: 8px;
      padding: 10px 12px; margin-top: 8px; cursor: pointer; position: relative;
    }
    .segment:active { background: #eef2ff; }
    .seg-tag { font-size: 11px; font-weight: 600; color: var(--primary); margin-bottom: 4px; }
    .seg-content { font-size: 13px; line-height: 1.5; color: #475569; word-break: break-word; white-space: pre-wrap; }
    .seg-copy-hint { font-size: 11px; color: var(--text-muted); text-align: right; margin-top: 4px; }
    
    /* 浮动提示 Toast */
    #toast {
      position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
      background: rgba(33, 37, 41, 0.9); color: white; padding: 8px 18px;
      border-radius: 20px; font-size: 13px; z-index: 1000; display: none;
    }
    
    /* 登录弹窗 */
    .auth-overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 999;
      display: flex; align-items: center; justify-content: center; padding: 20px;
    }
    .auth-card {
      background: white; width: 100%; max-width: 360px; border-radius: 16px;
      padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    .auth-card h2 { font-size: 18px; margin-bottom: 16px; text-align: center; color: var(--text); }
    .auth-input { width: 100%; border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; font-size: 14px; margin-bottom: 12px; outline: none; }
    .auth-btn {
      width: 100%; background: var(--primary); color: white; border: none;
      border-radius: 8px; padding: 10px; font-size: 15px; font-weight: 600; cursor: pointer;
    }
    .auth-toggle { text-align: center; margin-top: 14px; font-size: 13px; color: var(--text-muted); }
    .auth-toggle span { color: var(--primary); cursor: pointer; text-decoration: underline; }
    .empty-tip { text-align: center; padding: 50px 0; color: var(--text-muted); font-size: 14px; }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-logo">P</div>
      <span>PromptDock</span>
    </div>
    <div class="user-info" id="userBox">
      <span id="userEmail"></span>
      <button class="logout-btn" onclick="logout()">退出</button>
    </div>
  </header>

  <div class="toolbar">
    <input type="text" class="search-box" id="searchInput" placeholder="🔍 搜索提示词标题或内容..." oninput="filterPrompts()">
    <div class="folders-bar" id="foldersBar">
      <button class="folder-pill active" onclick="selectFolder('')">全部</button>
    </div>
  </div>

  <div class="container" id="cardsContainer">
    <div class="empty-tip">加载中...</div>
  </div>

  <div id="toast"></div>

  <!-- 登录 / 注册 浮层 -->
  <div class="auth-overlay" id="authModal" style="display: none;">
    <div class="auth-card">
      <h2 id="authTitle">登录 PromptDock</h2>
      <input type="email" id="authEmail" class="auth-input" placeholder="输入邮箱">
      <input type="password" id="authPassword" class="auth-input" placeholder="输入密码 (至少6位)">
      <button class="auth-btn" id="authSubmitBtn" onclick="submitAuth()">登录</button>
      <div class="auth-toggle" id="authToggle">还没有账号？<span onclick="toggleAuthMode()">立即注册</span></div>
    </div>
  </div>

  <script>
    let token = localStorage.getItem("promptdock_token");
    let currentEmail = localStorage.getItem("promptdock_email");
    let allPrompts = [];
    let activeFolder = "";
    let isRegisterMode = false;

    function showToast(msg) {
      const t = document.getElementById("toast");
      t.innerText = msg;
      t.style.display = "block";
      setTimeout(() => { t.style.display = "none"; }, 1500);
    }

    function checkAuth() {
      if (!token) {
        document.getElementById("authModal").style.display = "flex";
        document.getElementById("userBox").style.display = "none";
      } else {
        document.getElementById("authModal").style.display = "none";
        document.getElementById("userBox").style.display = "flex";
        document.getElementById("userEmail").innerText = currentEmail || "已登录";
        loadPrompts();
      }
    }

    function toggleAuthMode() {
      isRegisterMode = !isRegisterMode;
      document.getElementById("authTitle").innerText = isRegisterMode ? "注册 PromptDock" : "登录 PromptDock";
      document.getElementById("authSubmitBtn").innerText = isRegisterMode ? "立即注册" : "登录";
      document.getElementById("authToggle").innerHTML = isRegisterMode 
        ? "已有账号？<span onclick='toggleAuthMode()'>直接登录</span>"
        : "还没有账号？<span onclick='toggleAuthMode()'>立即注册</span>";
    }

    async function submitAuth() {
      const email = document.getElementById("authEmail").value.trim();
      const password = document.getElementById("authPassword").value.trim();
      if (!email || !password) {
        alert("请输入邮箱和密码");
        return;
      }
      const endpoint = isRegisterMode ? "/api/register" : "/api/login";
      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) {
          alert(data.error || "操作失败");
          return;
        }
        token = data.token;
        currentEmail = data.email;
        localStorage.setItem("promptdock_token", token);
        localStorage.setItem("promptdock_email", currentEmail);
        checkAuth();
      } catch (err) {
        alert("网络错误: " + err.message);
      }
    }

    function logout() {
      if (confirm("确定要退出登录吗？")) {
        localStorage.removeItem("promptdock_token");
        localStorage.removeItem("promptdock_email");
        token = null;
        currentEmail = null;
        checkAuth();
      }
    }

    async function loadPrompts() {
      try {
        const res = await fetch("/api/sync/pull?since=0", {
          headers: { "Authorization": "Bearer " + token }
        });
        if (res.status === 401) {
          logout();
          return;
        }
        const data = await res.json();
        allPrompts = (data.prompts || []).filter(p => !p.is_deleted);
        renderFolders();
        filterPrompts();
      } catch (err) {
        document.getElementById("cardsContainer").innerHTML = '<div class="empty-tip">加载失败，请刷新重试</div>';
      }
    }

    function renderFolders() {
      const folders = new Set();
      allPrompts.forEach(p => { if (p.folder) folders.add(p.folder); });
      const bar = document.getElementById("foldersBar");
      let html = '<button class="folder-pill ' + (activeFolder === "" ? "active" : "") + '" onclick="selectFolder(\\'\\')">全部 (' + allPrompts.length + ')</button>';
      folders.forEach(f => {
        const count = allPrompts.filter(p => p.folder === f).length;
        html += '<button class="folder-pill ' + (activeFolder === f ? "active" : "") + '" onclick="selectFolder(\\'' + f + '\\')">' + f + ' (' + count + ')</button>';
      });
      bar.innerHTML = html;
    }

    function selectFolder(f) {
      activeFolder = f;
      renderFolders();
      filterPrompts();
    }

    function copyText(text) {
      navigator.clipboard.writeText(text).then(() => {
        showToast("✅ 已复制到剪贴板");
      }).catch(() => {
        const ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        showToast("✅ 已复制");
      });
    }

    function filterPrompts() {
      const q = document.getElementById("searchInput").value.trim().toLowerCase();
      let list = allPrompts;
      if (activeFolder) {
        list = list.filter(p => p.folder === activeFolder);
      }
      if (q) {
        list = list.filter(p => {
          if (p.title.toLowerCase().includes(q)) return true;
          return (p.segments || []).some(s => s.content.toLowerCase().includes(q));
        });
      }

      list.sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0));

      const container = document.getElementById("cardsContainer");
      if (list.length === 0) {
        container.innerHTML = '<div class="empty-tip">未找到相关提示词</div>';
        return;
      }

      let html = "";
      list.forEach(p => {
        html += '<div class="card" style="border-left: 4px solid ' + (p.color || '#4361ee') + ';">';
        html += '  <div class="card-header">';
        html += '    <div class="card-title">' + escapeHtml(p.title) + '</div>';
        if (p.pinned) html += '    <span class="badge-pin">置顶</span>';
        html += '  </div>';

        (p.segments || []).forEach((seg, idx) => {
          html += '  <div class="segment" onclick="copyText(this.dataset.content)" data-content="' + escapeAttr(seg.content) + '">';
          if (p.segments.length > 1) {
            html += '    <div class="seg-tag">提示词 ' + (idx + 1) + '</div>';
          }
          html += '    <div class="seg-content">' + escapeHtml(seg.content) + '</div>';
          html += '    <div class="seg-copy-hint">👆 点击复制</div>';
          html += '  </div>';
        });

        html += '</div>';
      });
      container.innerHTML = html;
    }

    function escapeHtml(str) {
      return (str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }
    function escapeAttr(str) {
      return (str || "").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }

    checkAuth();
  </script>
</body>
</html>`;
}
