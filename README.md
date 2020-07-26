# ComBot
 ComBot or COMTRAN Bot is a bot that help creating a personal competitive programming contest where the problemset is taken from another online judge platform, currently this bot only support  online judge TLX (tlx.toki.id)


### ComBot's Command List

|Command|Description|
|:-|:-|
|tlx_contest+ `contest_name`|create contest|
|tlx_contest- `contest_id`|delete contest|
|tlx_contest `contest_id`|show contest|
|tlx_problem+ `contest_id` `problem_slug`|add problem to contest|
|tlx_problem- `contest_id` `problem_slug`|delete problem from contest|
|tlx_player+ `contest_id` `tlx_username`|register to the contest|
|tlx_player- `contest_id`|cancel the registration of contest|
|tlx_duration `contest_id` `duration`|set contest's duration|
|tlx_duration+ `contest_id` `duration`|extend contest's duration|
|tlx_scoreboard `contest_id`|show scoreboard|
|tlx_start `contest_id`|start contest|

Note :
- Problem that can be added to the contest is only from TLX problems, not TLX courses nor TLX contests.
- You can get `problem_slug` from TLX problems link and extract the last two argument
	
	For example, if you want add these problem [https://tlx.toki.id/problems/sg-noi-2020/A](https://tlx.toki.id/problems/sg-noi-2020/A), then the `problem_slug` will be `sg-noi-2020/A`

- You can get `contest_id` after you create a contest, ComBot will send a message that contain `contest_name` and `contest_id` with format like this

	>	`{contest_name}` #`{contest_id}` berhasil dibuat