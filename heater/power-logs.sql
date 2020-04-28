CREATE TABLE IF NOT EXISTS wemo_states (
    id serial PRIMARY KEY,
    name text UNIQUE NOT NULL
);

INSERT INTO wemo_states (name)
    VALUES ('on'), ('off'), ('standby')
    ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS wemo_records (
    time timestamp with time zone not null,
    state_id integer REFERENCES wemo_states(id),
    current_power_mw integer not null,
    last_state_change timestamp with time zone not null,
    on_for_seconds integer not null,
    on_today_seconds integer not null,
    on_total_seconds integer not null,
    power_threshold_mw integer not null,
    time_period integer not null,
    today_mw integer not null,
    total_mw integer not null,
    unknown integer not null
);
