insert into sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
values (2049629108253622287, 'dict.menu', 'PluginDict', '/plugins/dict', 8, 'fluent-mdl2:dictionary', 1, '/plugins/dict/views/index', null, 1, 1, 1, '', null, 2049629108245233667, now(), null);

insert into sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
values
(2049629108253622288, 'Add type', 'AddDictType', null, 0, null, 2, null, 'dict:type:add', 1, 0, 1, '', null, 2049629108253622287, now(), null),
(2049629108253622289, 'Edit type', 'EditDictType', null, 0, null, 2, null, 'dict:type:edit', 1, 0, 1, '', null, 2049629108253622287, now(), null),
(2049629108253622290, 'Delete type', 'DeleteDictType', null, 0, null, 2, null, 'dict:type:del', 1, 0, 1, '', null, 2049629108253622287, now(), null),
(2049629108253622291, 'Add entry', 'AddDictData', null, 0, null, 2, null, 'dict:data:add', 1, 0, 1, '', null, 2049629108253622287, now(), null),
(2049629108253622292, 'Edit entry', 'EditDictData', null, 0, null, 2, null, 'dict:data:edit', 1, 0, 1, '', null, 2049629108253622287, now(), null),
(2049629108253622293, 'Delete entry', 'DeleteDictData', null, 0, null, 2, null, 'dict:data:del', 1, 0, 1, '', null, 2049629108253622287, now(), null);

insert into sys_dict_type (id, name, code, remark, created_time, updated_time)
values
(2048602512340156416, 'General status', 'sys_status', 'General system status: 1/0', now(), null),
(2048602512369516544, 'General switch', 'sys_choose', 'General system switch: true/false', now(), null),
(2048602512432431104, 'Menu type', 'sys_menu_type', 'System menu type', now(), null),
(2048602512495345664, 'Login status', 'sys_login_status', 'User login status', now(), null),
(2048602512549871616, 'Data rule operator', 'sys_data_rule_operator', 'Data permission rule operator', now(), null),
(2048602512616980480, 'Data rule expression', 'sys_data_rule_expression', 'Data permission rule expression', now(), null),
(2048602512692477952, 'Frontend configuration parameters', 'sys_frontend_config', 'Frontend configuration parameter type', now(), null),
(2048602512755392512, 'Task schedule type', 'task_strategy_type', 'Scheduled task strategy type', now(), null),
(2048602512818307072, 'Task period type', 'task_period_type', 'Scheduled task period type', now(), null),
(2048602512881221632, 'Notices and announcements', 'notice', 'Notification type', now(), null),
(2048602512948330496, 'Online status', 'user_online_status', 'User online status', now(), null),
(2048602513015439360, 'Plugin type', 'sys_plugin_type', 'Plugin type', now(), null);

insert into sys_dict_data (id, type_code, label, value, color, sort, status, remark, type_id, created_time, updated_time)
values
(2048602513078353920, 'sys_status', 'Disabled', '0', 'red', 1, 1, 'Disabled status', 2048602512340156416, now(), null),
(2048602513128685568, 'sys_status', 'Enabled', '1', 'green', 2, 1, 'Enabled status', 2048602512340156416, now(), null),
(2048602513174822912, 'sys_choose', 'Off', 'false', 'error', 1, 1, 'Off status', 2048602512369516544, now(), null),
(2048602513241931776, 'sys_choose', 'On', 'true', 'success', 2, 1, 'On status', 2048602512369516544, now(), null),
(2048602513292263424, 'sys_menu_type', 'Directory', '0', 'orange', 1, 1, 'Menu directory', 2048602512432431104, now(), null),
(2048602513359372288, 'sys_menu_type', 'Menu', '1', 'default', 2, 1, 'Standard menu', 2048602512432431104, now(), null),
(2048602513422286848, 'sys_menu_type', 'Button', '2', 'processing', 3, 1, 'Menu button', 2048602512432431104, now(), null),
(2048602513476812800, 'sys_menu_type', 'Embedded', '3', 'cyan', 4, 1, 'Embedded page', 2048602512432431104, now(), null),
(2048602513543921664, 'sys_menu_type', 'External link', '4', 'purple', 5, 1, 'External link', 2048602512432431104, now(), null),
(2048602513590059008, 'sys_login_status', 'Failed', '0', 'error', 1, 1, 'Failed login status', 2048602512495345664, now(), null),
(2048602513657167872, 'sys_login_status', 'Successful', '1', 'success', 2, 1, 'Successful login status', 2048602512495345664, now(), null),
(2048602513720082432, 'sys_data_rule_operator', 'AND', '0', 'green', 1, 1, 'Logical AND operator', 2048602512549871616, now(), null),
(2048602513782996992, 'sys_data_rule_operator', 'OR', '1', 'gold', 2, 1, 'Logical OR operator', 2048602512549871616, now(), null),
(2048602513850105856, 'sys_data_rule_expression', 'Equal (==)', '0', 'success', 1, 1, 'Equality comparison', 2048602512616980480, now(), null),
(2048602513917214720, 'sys_data_rule_expression', 'Not equal (!=)', '1', 'error', 2, 1, 'Inequality comparison', 2048602512616980480, now(), null),
(2048602513984323584, 'sys_data_rule_expression', 'Greater than (>)', '2', 'magenta', 3, 1, 'Greater-than comparison', 2048602512616980480, now(), null),
(2048602514051432448, 'sys_data_rule_expression', 'Greater than or equal (>=)', '3', 'volcano', 4, 1, 'Greater-than-or-equal comparison', 2048602512616980480, now(), null),
(2048602514118541312, 'sys_data_rule_expression', 'Less than (<)', '4', 'gold', 5, 1, 'Less-than comparison', 2048602512616980480, now(), null),
(2048602514168872960, 'sys_data_rule_expression', 'Less than or equal (<=)', '5', 'orange', 6, 1, 'Less-than-or-equal comparison', 2048602512616980480, now(), null),
(2048602514231787520, 'sys_data_rule_expression', 'In (in)', '6', 'purple', 7, 1, 'Membership expression', 2048602512616980480, now(), null),
(2048602514303090688, 'sys_data_rule_expression', 'Not in (not in)', '7', 'error', 8, 1, 'Non-membership expression', 2048602512616980480, now(), null),
(2048602514366005248, 'sys_frontend_config', 'No', '0', 'red', 1, 1, 'Not a frontend configuration parameter', 2048602512692477952, now(), null),
(2048602514433114112, 'sys_frontend_config', 'Yes', '1', 'green', 2, 1, 'Frontend configuration parameter', 2048602512692477952, now(), null),
(2048602514500222976, 'task_strategy_type', 'Interval', '0', 'cyan', 1, 1, 'Time interval strategy', 2048602512755392512, now(), null),
(2048602514567331840, 'task_strategy_type', 'Crontab', '1', 'purple', 2, 1, 'Cron expression strategy', 2048602512755392512, now(), null),
(2048602514634440704, 'task_period_type', 'Days', 'days', 'processing', 1, 1, 'Scheduled task period type: days', 2048602512818307072, now(), null),
(2048602514701549568, 'task_period_type', 'Hours', 'hours', 'magenta', 2, 1, 'Scheduled task period type: hours', 2048602512818307072, now(), null),
(2048602514768658432, 'task_period_type', 'Minutes', 'minutes', 'volcano', 3, 1, 'Scheduled task period type: minutes', 2048602512818307072, now(), null),
(2048602514835767296, 'task_period_type', 'Seconds', 'seconds', 'gold', 4, 1, 'Scheduled task period type: seconds', 2048602512818307072, now(), null),
(2048602514902876160, 'task_period_type', 'Microseconds', 'microseconds', 'warning', 5, 1, 'Scheduled task period type: microseconds', 2048602512818307072, now(), null),
(2048602514969985024, 'notice', 'Notification', '0', 'magenta', 1, 1, 'Notification type', 2048602512881221632, now(), null),
(2048602515037093888, 'notice', 'Announcement', '1', 'purple', 2, 1, 'Announcement type', 2048602512881221632, now(), null),
(2048602515104202752, 'user_online_status', 'Offline', '0', 'warning', 1, 1, 'User offline status', 2048602512948330496, now(), null),
(2048602515171311616, 'user_online_status', 'Online', '1', 'success', 2, 1, 'User online status', 2048602512948330496, now(), null),
(2048602515238420480, 'sys_plugin_type', 'Archive', '0', 'gold', 1, 1, 'Plugin type: archive', 2048602513015439360, now(), null),
(2048602515305529344, 'sys_plugin_type', 'GIT', '1', 'processing', 2, 1, 'Plugin type: Git', 2048602513015439360, now(), null);
