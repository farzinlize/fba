do $$
declare
    config_menu_id bigint;
begin
    insert into sys_menu (title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
    values ('config.menu', 'PluginConfig', '/plugins/config', 7, 'codicon:symbol-parameter', 1, '/plugins/config/views/index', null, 1, 1, 1, '', null, (select id from sys_menu where name = 'System'), now(), null)
    returning id into config_menu_id;

    insert into sys_menu (title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
    values
    ('Add', 'AddConfig', null, 0, null, 2, null, 'sys:config:add', 1, 0, 1, '', null, config_menu_id, now(), null),
    ('Edit', 'EditConfig', null, 0, null, 2, null, 'sys:config:edit', 1, 0, 1, '', null, config_menu_id, now(), null),
    ('Delete', 'DeleteConfig', null, 0, null, 2, null, 'sys:config:del', 1, 0, 1, '', null, config_menu_id, now(), null);
end $$;

select setval(pg_get_serial_sequence('sys_menu', 'id'), coalesce(max(id), 0) + 1, true) from sys_menu;

insert into sys_config (id, name, type, "key", value, is_frontend, remark, created_time, updated_time)
values
(1, 'Status', 'EMAIL', 'EMAIL_CONFIG_STATUS', '1', false, null, now(), null),
(2, 'Server address', 'EMAIL', 'EMAIL_HOST', 'smtp.qq.com', false, null, now(), null),
(3, 'Server port', 'EMAIL', 'EMAIL_PORT', '465', false, null, now(), null),
(4, 'Email account', 'EMAIL', 'EMAIL_USERNAME', 'fba@qq.com', false, null, now(), null),
(5, 'Email password', 'EMAIL', 'EMAIL_PASSWORD', '', false, null, now(), null),
(6, 'SSL encryption', 'EMAIL', 'EMAIL_SSL', 'true', false, null, now(), null),
(7, 'Status', 'USER_SECURITY', 'USER_SECURITY_CONFIG_STATUS', '1', false, null, now(), null),
(8, 'Failed password attempt limit', 'USER_SECURITY', 'USER_LOCK_THRESHOLD', '5', false, '0 disables account lockout', now(), null),
(9, 'Password lockout duration (seconds)', 'USER_SECURITY', 'USER_LOCK_SECONDS', '300', false, null, now(), null),
(10, 'Password validity period (days)', 'USER_SECURITY', 'USER_PASSWORD_EXPIRY_DAYS', '365', false, '0 means never expires', now(), null),
(11, 'Password expiration reminder (days)', 'USER_SECURITY', 'USER_PASSWORD_REMINDER_DAYS', '7', false, '0 disables reminders', now(), null),
(12, 'Password history check count', 'USER_SECURITY', 'USER_PASSWORD_HISTORY_CHECK_COUNT', '3', false, null, now(), null),
(13, 'Minimum password length', 'USER_SECURITY', 'USER_PASSWORD_MIN_LENGTH', '6', false, null, now(), null),
(14, 'Maximum password length', 'USER_SECURITY', 'USER_PASSWORD_MAX_LENGTH', '32', false, null, now(), null),
(15, 'Password must contain a special character', 'USER_SECURITY', 'USER_PASSWORD_REQUIRE_SPECIAL_CHAR', 'false', false, null, now(), null),
(16, 'Status', 'LOGIN', 'LOGIN_CONFIG_STATUS', '1', false, null, now(), null),
(17, 'CAPTCHA enabled', 'LOGIN', 'LOGIN_CAPTCHA_ENABLED', 'true', false, null, now(), null);

select setval(pg_get_serial_sequence('sys_config', 'id'),coalesce(max(id), 0) + 1, true) from sys_config;
