# PromptDock Cloudflare 云端部署指南

PromptDock 云端由 **Cloudflare Worker** + **Cloudflare D1（免费云数据库）** 组成，终身免费，永不丢数据。

你可以在 **命令行一键部署（推荐）** 或 **在 Cloudflare 网页后台操作**。

---

## 方式一：命令行一键部署（最快最简单）

打开命令行提示符（CMD），进入此文件夹：

```cmd
cd /d d:\PromptDock\cf-worker
```

### 第 1 步：登录你的 Cloudflare 账号
```cmd
cmd /c npx wrangler login
```
*浏览器会自动弹出一个授权页面，点击「允许/Authorize」即可完成登录。*

### 第 2 步：创建一个免费的 D1 数据库
```cmd
cmd /c npx wrangler d1 create promptdock-db
```
执行后，控制台会输出类似下面的一段文字：
```toml
[[d1_databases]]
binding = "DB"
database_name = "promptdock-db"
database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```
**复制上面的 `database_id`，打开同目录下的 `wrangler.toml` 文件，把 `YOUR_D1_DATABASE_ID` 替换为这个真实 ID。**

### 第 3 步：初始化数据库表结构
```cmd
cmd /c npx wrangler d1 execute promptdock-db --file=schema.sql --remote
```

### 第 4 步：一键发布上线
```cmd
cmd /c npx wrangler deploy
```
发布完成后，控制台会输出一个访问链接，例如：
`https://promptdock-api.<你的前缀>.workers.dev`

🎉 **大功告成！** 
- 打开这个网址，就是你的**随身 Web 端**（手机/电脑打开都能看）；
- 把这个网址复制到 PromptDock 客户端的云同步设置里，就能全自动多端同步了！

---

## 方式二：在 Cloudflare 网页后台手动创建

如果你不想在电脑上敲命令，也可以完全在网页上点一点：

1. 打开 [Cloudflare 仪表盘 (dash.cloudflare.com)](https://dash.cloudflare.com/)；
2. 点击左侧菜单中的 **Workers & Pages** -> **D1 SQL Database** -> **Create database**：
   - 数据库名字填：`promptdock-db`；
   - 创建后，点击进入该数据库，切换到 **Console**（控制台）标签页，把 `schema.sql` 里的所有内容复制粘贴进去，点击 **Execute** 执行建表。
3. 返回 **Workers & Pages** -> **Overview** -> **Create application** -> **Create Worker**：
   - 命名为 `promptdock-api`，点击保存；
   - 点击 **Edit code**，将 `worker.js` 中的全部代码全选替换进去，点击 **Deploy**；
4. 绑定数据库：
   - 在该 Worker 详情页中，点击 **Settings** -> **Variables and Secrets** -> 找到 **D1 Database Bindings** -> **Add binding**：
   - Variable name (变量名) 填：`DB`；
   - D1 Database 选择刚才创建的 `promptdock-db`；
   - 点击保存并重新部署即可！

---

## 🔒 高级安全防护（防批量注册 / 私有部署）

已在 `worker.js` 中内置以下安全屏障：
- **IP 边缘频次限制**：单个 IP 10 分钟内限最多注册 3 次，防止机器人批量刷爆免费配额；
- **防暴力破解**：同一账号连续输错 5 次密码自动临时锁定 5 分钟；
- **白名单参数校验**：严格限制邮箱规范、密码长度 (6~64位)、头像大小 (100KB内) 与单次同步条目；
- **私有邀请码机制（可选）**：若希望仅供自己或朋友使用，可在 Cloudflare Worker 环境变量添加 `INVITE_CODE`；
- **一键关闭注册（可选）**：若已注册好主账号、想彻底杜绝外部注册，可在 Cloudflare Worker 环境变量设置 `REGISTRATION_DISABLED = "true"`。

