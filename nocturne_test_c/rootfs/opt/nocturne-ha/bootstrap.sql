-- Bootstrap owned by this wrapper; runs only before the first API migration.
-- Values are passed as psql variables, never interpolated in SQL by the shell.
BEGIN;
CREATE ROLE nocturne_migrator LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE PASSWORD :'migrator_password';
CREATE ROLE nocturne_app LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE PASSWORD :'app_password';
CREATE ROLE nocturne_web LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE PASSWORD :'web_password';
ALTER DATABASE nocturne OWNER TO nocturne_migrator;
ALTER SCHEMA public OWNER TO nocturne_migrator;
GRANT CONNECT ON DATABASE nocturne TO nocturne_app;
GRANT USAGE ON SCHEMA public TO nocturne_app;
GRANT CONNECT ON DATABASE nocturne TO nocturne_web;
GRANT USAGE, CREATE ON SCHEMA public TO nocturne_web;
ALTER DEFAULT PRIVILEGES FOR ROLE nocturne_migrator IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO nocturne_app;
ALTER DEFAULT PRIVILEGES FOR ROLE nocturne_migrator IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO nocturne_app;
COMMIT;
