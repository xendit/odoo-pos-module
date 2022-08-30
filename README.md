# Xendit Odoo POS
Xendit Odoo POS is payment addon

## Ownership

Team: [TPI Team](https://www.draw.io/?state=%7B%22ids%22:%5B%221Vk1zqYgX2YqjJYieQ6qDPh0PhB2yAd0j%22%5D,%22action%22:%22open%22,%22userId%22:%22104938211257040552218%22%7D)

Slack Channel: [#p-integration](https://xendit.slack.com/archives/CFJ9Q3NKY)

Slack Mentions: `@troops-tpi`

## How to run?
1. Open terminal, run `docker-compose up`
2. Open http://localhost:8069/ in browser

## How to enable developer mode
Add debug=1 query (?debug=1) in web url
e.g: http://localhost:8069/web?debug=1%2Fweb#action=35&cids=1&menu_id=5&model=ir.module.module&view_type=kanban

## How to show Xendit POS
1. Enable developer mode
2. Click Update Apps list and Update button
<img width="1792" alt="Screen Shot 2022-07-27 at 15 37 29" src="https://user-images.githubusercontent.com/9255677/181202902-375784bb-baa8-4a05-8592-fe341728b4a7.png">

3. Click Install
<img width="1792" alt="Screen Shot 2022-07-27 at 15 42 23" src="https://user-images.githubusercontent.com/9255677/181203086-26929bd4-d4d8-4b5c-aabd-9251b5464928.png">

## Note:
- If you're using Odoo `14.x`, you should switch to branch `14.0` to get the correct version compatible with your Odoo
