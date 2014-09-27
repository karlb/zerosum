DROP FUNCTION IF EXISTS recent_owes(current_user_id bigint);
CREATE OR REPLACE FUNCTION recent_owes(current_user_id bigint)
RETURNS TABLE (
    user_id bigint,
    usr json,
    amount decimal,
    subject text,
    created_at timestamp,
    currency text,
    is_new bool
) AS $$
    SELECT user_id,
        row_to_json(zerosum_user),
        CASE
            WHEN creditor_id = current_user_id THEN amount
            ELSE -amount
        END AS amount,
        subject,
        created_at,
        currency,
        created_at > now() - INTERVAL '1 day' AS is_new
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
    ORDER BY created_at DESC
$$ LANGUAGE sql;


DROP FUNCTION IF EXISTS balances(current_user_id bigint);
CREATE OR REPLACE FUNCTION balances(current_user_id bigint)
RETURNS TABLE (
    user_id bigint,
    usr json,
    amount decimal,
    currency text,
    latest timestamp
) AS $$
    SELECT user_id,
        usr::text::json,
        sum(amount),
        currency,
        max(created_at) AS latest
    FROM recent_owes(current_user_id)
    GROUP BY user_id, usr::text, currency
    ORDER BY latest DESC
$$ LANGUAGE sql;


/*
CREATE OR REPLACE FUNCTION clear_balance(p_user_id bigint)
RETURNS bigint
AS $$
    SELECT *
    FROM (
            SELECT *
            FROM balances(1)
        ) b1,
        balances(user_id)
$$ LANGUAGE sql;


WITH RECURSIVE possible_clearing AS (
    SELECT 0 AS iteration, 'inf'::float AS amount, ARRAY[]::bigint[] AS users,
        1::bigint AS last_user_id, false AS has_cycle
    UNION ALL
    SELECT iteration + 1, least(c.amount, abs(b.amount)), array_append(users, b.user_id),
           b.user_id, b.user_id = 1
    FROM possible_clearing c,
         balances(last_user_id) b
    WHERE iteration < 5
      AND b.amount < 0
)
SELECT * FROM possible_clearing
WHERE has_cycle
LIMIT 1
;
*/
