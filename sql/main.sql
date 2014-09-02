DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
--CREATE EXTENSION "uuid-ossp";


CREATE TABLE zerosum_user (
    user_id bigserial PRIMARY KEY,
    name text,
    email text UNIQUE,
    is_active bool DEFAULT false,
    password_hash text
);

ALTER SEQUENCE zerosum_user_user_id_seq RESTART WITH 10;
-- password is 'foo' for the following users
INSERT INTO zerosum_user VALUES (1, 'u1', 'u1@example.com', true, 'pbkdf2:sha1:1000$QIlMjr3h$3ce22bbce5ac3ade5406a7bd8040e01ab41cddaa');
INSERT INTO zerosum_user VALUES (2, 'u2', 'u2@example.com', true, 'pbkdf2:sha1:1000$QIlMjr3h$3ce22bbce5ac3ade5406a7bd8040e01ab41cddaa');
INSERT INTO zerosum_user VALUES (3, 'u3', 'u3@example.com', false, 'pbkdf2:sha1:1000$QIlMjr3h$3ce22bbce5ac3ade5406a7bd8040e01ab41cddaa');


CREATE TABLE owe (
    owe_id bigserial PRIMARY KEY,
    creditor_id bigint REFERENCES zerosum_user(user_id) NOT NULL,
    debitor_id bigint REFERENCES zerosum_user(user_id) NOT NULL,
    amount decimal NOT NULL CHECK (amount > 0),
    subject text,
    created timestamp NOT NULL DEFAULT (now() at time zone 'utc'),
    currency text NOT NULL DEFAULT 'EUR'
);

INSERT INTO owe(creditor_id, debitor_id, amount, subject) VALUES 
    (1, 2, 11.40, 'Brunch'),
    (1, 2, 3.00, 'Döner'),
    (2, 1, 5.80, 'Thanks for the Cocktail')
;


CREATE OR REPLACE FUNCTION gen_uuid()
RETURNS uuid AS $$
  SELECT uuid_in(md5(random()::text || now()::text)::cstring);
$$ LANGUAGE sql;


CREATE TABLE email_confirm (
    --code uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    code uuid DEFAULT gen_uuid() PRIMARY KEY,
    email text NOT NULL,
    created timestamp NOT NULL DEFAULT (now() at time zone 'utc'),
    opened timestamp
);

INSERT INTO email_confirm(email, code) VALUES ('u3@example.com', '123e4567-e89b-12d3-a456-426655440000');


CREATE OR REPLACE FUNCTION recent_owes(current_user_id bigint)
RETURNS TABLE (
    user_id bigint,
    user_name text,
    amount decimal,
    subject text,
    created timestamp,
    currency text,
    is_new bool
) AS $$
    SELECT user_id,
        name,
        CASE
            WHEN creditor_id = current_user_id THEN amount
            ELSE -amount
        END AS amount,
        subject,
        created,
        currency,
        created > now() - INTERVAL '1 day' AS is_new
    FROM owe
        JOIN zerosum_user ON (
            (
                debitor_id = current_user_id
                AND user_id = creditor_id
            ) OR (
                creditor_id = current_user_id
                AND user_id = debitor_id
            )
        )
    ORDER BY created DESC
$$ LANGUAGE sql;


CREATE OR REPLACE FUNCTION balances(current_user_id bigint)
RETURNS TABLE (
    user_id bigint,
    user_name text,
    amount decimal,
    currency text,
    latest timestamp
) AS $$
    SELECT user_id,
        user_name,
        sum(amount),
        currency,
        max(created) AS latest
    FROM recent_owes(current_user_id)
    GROUP BY user_id, user_name, currency
$$ LANGUAGE sql;


--CREATE OR REPLACE FUNCTION create_owe(current_user_id, )
