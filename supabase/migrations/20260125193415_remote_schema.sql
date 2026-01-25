drop extension if exists "pg_net";

alter table "public"."calendar_events" alter column "timezone" set default 'UTC'::text;


