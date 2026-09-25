do $$
declare
    codegen_menu_id bigint;
begin
    insert into sys_menu (title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
    values ('code-generator.menu', 'PluginCodeGenerator', '/plugins/code-generator', 10, 'tabler:code', 1, '/plugins/code-generator/views/index', null, 1, 1, 1, '', null, null, now(), null)
    returning id into codegen_menu_id;

    insert into sys_menu (title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
    values
    ('Add business definition', 'AddGenCodeBusiness', null, 0, null, 2, null, 'codegen:business:add', 1, 0, 1, '', null, codegen_menu_id, now(), null),
    ('Edit business definition', 'EditGenCodeBusiness', null, 0, null, 2, null, 'codegen:business:edit', 1, 0, 1, '', null, codegen_menu_id, now(), null),
    ('Delete business definition', 'DeleteGenCodeBusiness', null, 0, null, 2, null, 'codegen:business:del', 1, 0, 1, '', null, codegen_menu_id, now(), null),
    ('Add model', 'AddGenCodeModel', null, 0, null, 2, null, 'codegen:model:add', 1, 0, 1, '', null, codegen_menu_id, now(), null),
    ('Edit model', 'EditGenCodeModel', null, 0, null, 2, null, 'codegen:model:edit', 1, 0, 1, '', null, codegen_menu_id, now(), null),
    ('Delete model', 'DeleteGenCodeModel', null, 0, null, 2, null, 'codegen:model:del', 1, 0, 1, '', null, codegen_menu_id, now(), null),
    ('Import', 'ImportGenCode', null, 0, null, 2, null, 'codegen:table:import', 1, 0, 1, '', null, codegen_menu_id, now(), null),
    ('Write', 'WriteGenCode', null, 0, null, 2, null, 'codegen:local:write', 1, 0, 1, '', null, codegen_menu_id, now(), null);
end $$;

select setval(pg_get_serial_sequence('sys_menu', 'id'), coalesce(max(id), 0) + 1, true) from sys_menu;

insert into code_gen_business (id, app_name, table_name, doc_comment, table_comment, class_name, schema_name, filename, datetime_mixin, api_version, gen_path, remark, created_time, updated_time)
values (1, 'test', 'sys_opera_log', 'Operation log table', 'Operation log table', 'SysOperaLog', 'SysOperaLog', 'sys_opera_log', true, 'v1', null, null, '2025-12-15 15:30:33', null);

insert into code_gen_column (id, name, comment, type, pd_type, "default", sort, "length", is_pk, is_nullable, code_gen_business_id)
values
(1, 'trace_id', 'Request trace ID', 'String', 'str', null, 2, 32, false, false, 1),
(2, 'username', 'Username', 'String', 'str', null, 3, 64, false, true, 1),
(3, 'method', 'Request type', 'String', 'str', null, 4, 32, false, false, 1),
(4, 'title', 'Operation module', 'String', 'str', null, 5, 256, false, false, 1),
(5, 'path', 'Request path', 'String', 'str', null, 6, 512, false, false, 1),
(6, 'ip', 'IP address', 'String', 'str', null, 7, 64, false, false, 1),
(7, 'country', 'Country', 'String', 'str', null, 8, 64, false, true, 1),
(8, 'region', 'Region', 'String', 'str', null, 9, 64, false, true, 1),
(9, 'city', 'City', 'String', 'str', null, 10, 64, false, true, 1),
(10, 'user_agent', 'Request headers', 'String', 'str', null, 11, 512, false, false, 1),
(11, 'os', 'Operating system', 'String', 'str', null, 12, 64, false, true, 1),
(12, 'browser', 'Browser', 'String', 'str', null, 13, 64, false, true, 1),
(13, 'device', 'Device', 'String', 'str', null, 14, 64, false, true, 1),
(14, 'args', 'Request parameters', 'JSON', 'dict', null, 15, 0, false, true, 1),
(15, 'status', 'Operation status (0: error, 1: normal)', 'INTEGER', 'int', null, 16, 0, false, false, 1),
(16, 'code', 'Operation status code', 'String', 'str', null, 17, 32, false, false, 1),
(17, 'msg', 'Message', 'TEXT', 'str', null, 18, 0, false, true, 1),
(18, 'cost_time', 'Request duration (ms)', 'String', 'str', null, 19, 0, false, false, 1),
(19, 'opera_time', 'Operation time', 'String', 'str', null, 20, 0, false, false, 1);

select setval(pg_get_serial_sequence('code_gen_business', 'id'),coalesce(max(id), 0) + 1, true) from code_gen_business;
select setval(pg_get_serial_sequence('code_gen_column', 'id'),coalesce(max(id), 0) + 1, true) from code_gen_column;
