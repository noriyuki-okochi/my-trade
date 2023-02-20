begin transaction;
alter table trigger add column exectype text default 'LIMIT';
commit;
