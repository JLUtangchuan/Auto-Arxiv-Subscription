# Auto-Arxiv-Subscription
自动向邮箱按关键词发送相关主题的arxiv最新论文, 依赖与github action无需额外租服务器
### Usage
1. Fork本仓库
2. 配置参数
   - 在本仓库的Settings中找到Secrets->Actions
   - New repository secret
     - EMAIL          (邮件发送方: 推荐输出QQ邮箱)
     - EMAIL_TOKEN    (邮件授权码: 在邮箱设置中找到)
     - RECEIVER_EMAIL (邮件接收方: 个人的任意邮箱)
     - KEYWORDS       (查询关键词: 可以是多个关键词, 以空格分隔)
     - DASHSCOPE_API_KEY (信息提取API)
3. 点击Action, 查看workflow是否建立成功, 如果失败可以Re-run
4. 在邮箱中查看是否收到邮件
> 每天早七点自动发邮件, 请在[这里](https://github.com/JLUtangchuan/Auto-Arxiv-Subscription/blob/main/.github/workflows/actions.yml#L8)修改更改时间


## hot words

```
3D BEV occupancy instance segment point cloud detect Nerf transform autonomous driving Multi-Camera map lane planning
```