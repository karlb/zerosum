DROP FUNCTION IF EXISTS recent_owes(current_user_id bigint);
CREATE OR REPLACE FUNCTION recent_owes(current_user_id bigint)
RETURNS TABLE (
    user_id bigint,
    usr json,
    amount decimal,
    subject text,
    created timestamp,
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
        max(created) AS latest
    FROM recent_owes(current_user_id)
    GROUP BY user_id, usr::text, currency
    ORDER BY latest DESC
$$ LANGUAGE sql;
