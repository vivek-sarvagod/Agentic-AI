CREATE DATABASE IF NOT EXISTS portal_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE portal_db;

CREATE TABLE IF NOT EXISTS surveys (
    id              INT             NOT NULL AUTO_INCREMENT,
    first_name      VARCHAR(100)    NOT NULL,
    last_name       VARCHAR(100)    NOT NULL,
    street_address  VARCHAR(255)    NOT NULL,
    city            VARCHAR(100)    NOT NULL,
    state           VARCHAR(50)     NOT NULL,
    zip_code        VARCHAR(10)     NOT NULL,
    telephone       VARCHAR(20)     NOT NULL,
    email           VARCHAR(150)    NOT NULL,
    date_of_survey  DATE            NOT NULL,
    -- Comma-separated subset of: students, location, campus, atmosphere, dorm_rooms, sports
    liked_most      VARCHAR(255)    NOT NULL,
    -- One of: friends, television, internet, other
    interest_source VARCHAR(50)     NOT NULL,
    -- One of: Very Likely, Likely, Unlikely
    recommendation  VARCHAR(20)     NOT NULL,
    raffle          VARCHAR(255)    NULL,
    comments        TEXT            NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
