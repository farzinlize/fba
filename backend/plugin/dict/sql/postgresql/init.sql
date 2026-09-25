do $$
declare
    dict_menu_id bigint;
begin
    insert into sys_menu (title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
    values ('dict.menu', 'PluginDict', '/plugins/dict', 8, 'fluent-mdl2:dictionary', 1, '/plugins/dict/views/index', null, 1, 1, 1, '', null, (select id from sys_menu where name = 'System'), now(), null)
    returning id into dict_menu_id;

    insert into sys_menu (title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
    values
    ('Add type', 'AddDictType', null, 0, null, 2, null, 'dict:type:add', 1, 0, 1, '', null, dict_menu_id, now(), null),
    ('Edit type', 'EditDictType', null, 0, null, 2, null, 'dict:type:edit', 1, 0, 1, '', null, dict_menu_id, now(), null),
    ('Delete type', 'DeleteDictType', null, 0, null, 2, null, 'dict:type:del', 1, 0, 1, '', null, dict_menu_id, now(), null),
    ('Add entry', 'AddDictData', null, 0, null, 2, null, 'dict:data:add', 1, 0, 1, '', null, dict_menu_id, now(), null),
    ('Edit entry', 'EditDictData', null, 0, null, 2, null, 'dict:data:edit', 1, 0, 1, '', null, dict_menu_id, now(), null),
    ('Delete entry', 'DeleteDictData', null, 0, null, 2, null, 'dict:data:del', 1, 0, 1, '', null, dict_menu_id, now(), null);
end $$;

select setval(pg_get_serial_sequence('sys_menu', 'id'), coalesce(max(id), 0) + 1, true) from sys_menu;

insert into sys_dict_type (id, name, code, remark, created_time, updated_time)
values
(1, 'General status', 'sys_status', 'General system status: 1/0', now(), null),
(2, 'General switch', 'sys_choose', 'General system switch: true/false', now(), null),
(3, 'Menu type', 'sys_menu_type', 'System menu type', now(), null),
(4, 'Login status', 'sys_login_status', 'User login status', now(), null),
(5, 'Data rule operator', 'sys_data_rule_operator', 'Data permission rule operator', now(), null),
(6, 'Data rule expression', 'sys_data_rule_expression', 'Data permission rule expression', now(), null),
(7, 'Frontend configuration parameters', 'sys_frontend_config', 'Frontend configuration parameter type', now(), null),
(8, 'Task schedule type', 'task_strategy_type', 'Scheduled task strategy type', now(), null),
(9, 'Task period type', 'task_period_type', 'Scheduled task period type', now(), null),
(10, 'Notices and announcements', 'notice', 'Notification type', now(), null),
(11, 'Online status', 'user_online_status', 'User online status', now(), null),
(12, 'Plugin type', 'sys_plugin_type', 'Plugin type', now(), null);

insert into sys_dict_data (id, type_code, label, value, color, sort, status, remark, type_id, created_time, updated_time)
values
(1, 'sys_status', 'Disabled', '0', 'red', 1, 1, 'Disabled status', 1, now(), null),
(2, 'sys_status', 'Enabled', '1', 'green', 2, 1, 'Enabled status', 1, now(), null),
(3, 'sys_choose', 'Off', 'false', 'error', 1, 1, 'Off status', 2, now(), null),
(4, 'sys_choose', 'On', 'true', 'success', 2, 1, 'On status', 2, now(), null),
(5, 'sys_menu_type', 'Directory', '0', 'orange', 1, 1, 'Menu directory', 3, now(), null),
(6, 'sys_menu_type', 'Menu', '1', 'default', 2, 1, 'Standard menu', 3, now(), null),
(7, 'sys_menu_type', 'Button', '2', 'processing', 3, 1, 'Menu button', 3, now(), null),
(8, 'sys_menu_type', 'Embedded', '3', 'cyan', 4, 1, 'Embedded page', 3, now(), null),
(9, 'sys_menu_type', 'External link', '4', 'purple', 5, 1, 'External link', 3, now(), null),
(10, 'sys_login_status', 'Failed', '0', 'error', 1, 1, 'Failed login status', 4, now(), null),
(11, 'sys_login_status', 'Successful', '1', 'success', 2, 1, 'Successful login status', 4, now(), null),
(12, 'sys_data_rule_operator', 'AND', '0', 'green', 1, 1, 'Logical AND operator', 5, now(), null),
(13, 'sys_data_rule_operator', 'OR', '1', 'gold', 2, 1, 'Logical OR operator', 5, now(), null),
(14, 'sys_data_rule_expression', 'Equal (==)', '0', 'success', 1, 1, 'Equality comparison', 6, now(), null),
(15, 'sys_data_rule_expression', 'Not equal (!=)', '1', 'error', 2, 1, 'Inequality comparison', 6, now(), null),
(16, 'sys_data_rule_expression', 'Greater than (>)', '2', 'magenta', 3, 1, 'Greater-than comparison', 6, now(), null),
(17, 'sys_data_rule_expression', 'Greater than or equal (>=)', '3', 'volcano', 4, 1, 'Greater-than-or-equal comparison', 6, now(), null),
(18, 'sys_data_rule_expression', 'Less than (<)', '4', 'gold', 5, 1, 'Less-than comparison', 6, now(), null),
(19, 'sys_data_rule_expression', 'Less than or equal (<=)', '5', 'orange', 6, 1, 'Less-than-or-equal comparison', 6, now(), null),
(20, 'sys_data_rule_expression', 'In (in)', '6', 'purple', 7, 1, 'Membership expression', 6, now(), null),
(21, 'sys_data_rule_expression', 'Not in (not in)', '7', 'error', 8, 1, 'Non-membership expression', 6, now(), null),
(22, 'sys_frontend_config', 'No', '0', 'red', 1, 1, 'Not a frontend configuration parameter', 7, now(), null),
(23, 'sys_frontend_config', 'Yes', '1', 'green', 2, 1, 'Frontend configuration parameter', 7, now(), null),
(24, 'task_strategy_type', 'Interval', '0', 'cyan', 1, 1, 'Time interval strategy', 8, now(), null),
(25, 'task_strategy_type', 'Crontab', '1', 'purple', 2, 1, 'Cron expression strategy', 8, now(), null),
(26, 'task_period_type', 'Days', 'days', 'processing', 1, 1, 'Scheduled task period type: days', 9, now(), null),
(27, 'task_period_type', 'Hours', 'hours', 'magenta', 2, 1, 'Scheduled task period type: hours', 9, now(), null),
(28, 'task_period_type', 'Minutes', 'minutes', 'volcano', 3, 1, 'Scheduled task period type: minutes', 9, now(), null),
(29, 'task_period_type', 'Seconds', 'seconds', 'gold', 4, 1, 'Scheduled task period type: seconds', 9, now(), null),
(30, 'task_period_type', 'Microseconds', 'microseconds', 'warning', 5, 1, 'Scheduled task period type: microseconds', 9, now(), null),
(31, 'notice', 'Notification', '0', 'magenta', 1, 1, 'Notification type', 10, now(), null),
(32, 'notice', 'Announcement', '1', 'purple', 2, 1, 'Announcement type', 10, now(), null),
(33, 'user_online_status', 'Offline', '0', 'warning', 1, 1, 'User offline status', 11, now(), null),
(34, 'user_online_status', 'Online', '1', 'success', 2, 1, 'User online status', 11, now(), null),
(35, 'sys_plugin_type', 'Archive', '0', 'gold', 1, 1, 'Plugin type: archive', 12, now(), null),
(36, 'sys_plugin_type', 'GIT', '1', 'processing', 2, 1, 'Plugin type: Git', 12, now(), null);

select setval(pg_get_serial_sequence('sys_dict_type', 'id'),coalesce(max(id), 0) + 1, true) from sys_dict_type;
select setval(pg_get_serial_sequence('sys_dict_data', 'id'),coalesce(max(id), 0) + 1, true) from sys_dict_data;
