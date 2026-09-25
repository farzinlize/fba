insert into sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
values (2049629108253622283, 'config.menu', 'PluginConfig', '/plugins/config', 7, 'codicon:symbol-parameter', 1, '/plugins/config/views/index', null, 1, 1, 1, '', null, 2049629108245233667, now(), null);

insert into sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
values
(2049629108253622284, 'Add', 'AddConfig', null, 0, null, 2, null, 'sys:config:add', 1, 0, 1, '', null, 2049629108253622283, now(), null),
(2049629108253622285, 'Edit', 'EditConfig', null, 0, null, 2, null, 'sys:config:edit', 1, 0, 1, '', null, 2049629108253622283, now(), null),
(2049629108253622286, 'Delete', 'DeleteConfig', null, 0, null, 2, null, 'sys:config:del', 1, 0, 1, '', null, 2049629108253622283, now(), null);

insert into sys_config (id, name, type, "key", value, is_frontend, remark, created_time, updated_time)
values
(2069061886627938304, 'Status', 'EMAIL', 'EMAIL_CONFIG_STATUS', '1', false, null, now(), null),
(2069061886627938305, 'Server address', 'EMAIL', 'EMAIL_HOST', 'smtp.qq.com', false, null, now(), null),
(2069061886627938306, 'Server port', 'EMAIL', 'EMAIL_PORT', '465', false, null, now(), null),
(2069061886627938307, 'Email account', 'EMAIL', 'EMAIL_USERNAME', 'fba@qq.com', false, null, now(), null),
(2069061886627938308, 'Email password', 'EMAIL', 'EMAIL_PASSWORD', '', false, null, now(), null),
(2069061886627938309, 'SSL encryption', 'EMAIL', 'EMAIL_SSL', 'true', false, null, now(), null),
(2069061886627938310, 'Status', 'USER_SECURITY', 'USER_SECURITY_CONFIG_STATUS', '1', false, null, now(), null),
(2069061886627938311, 'Failed password attempt limit', 'USER_SECURITY', 'USER_LOCK_THRESHOLD', '5', false, '0 disables account lockout', now(), null),
(2069061886627938312, 'Password lockout (seconds)', 'USER_SECURITY', 'USER_LOCK_SECONDS', '300', false, null, now(), null),
(2069061886627938313, 'Password validity period (days)', 'USER_SECURITY', 'USER_PASSWORD_EXPIRY_DAYS', '365', false, '0 means never expires', now(), null),
(2069061886627938314, 'Password expiry reminder (days)', 'USER_SECURITY', 'USER_PASSWORD_REMINDER_DAYS', '7', false, '0 disables reminders', now(), null),
(2069061886627938315, 'Password history check count', 'USER_SECURITY', 'USER_PASSWORD_HISTORY_CHECK_COUNT', '3', false, null, now(), null),
(2069061886627938316, 'Minimum password length', 'USER_SECURITY', 'USER_PASSWORD_MIN_LENGTH', '6', false, null, now(), null),
(2069061886627938317, 'Maximum password length', 'USER_SECURITY', 'USER_PASSWORD_MAX_LENGTH', '32', false, null, now(), null),
(2069061886627938318, 'Require special password char', 'USER_SECURITY', 'USER_PASSWORD_REQUIRE_SPECIAL_CHAR', 'false', false, null, now(), null),
(2069061886627938319, 'Status', 'LOGIN', 'LOGIN_CONFIG_STATUS', '1', false, null, now(), null),
(2069061886627938320, 'CAPTCHA enabled', 'LOGIN', 'LOGIN_CAPTCHA_ENABLED', 'true', false, null, now(), null);
