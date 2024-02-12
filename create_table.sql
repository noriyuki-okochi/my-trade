drop table if exists balance;
create table if not exists balance( exchange text NOT NULL,
                                    symbol text NOT NULL,
                                    amount real,
                                    rate real, 
                                    updated_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    PRIMARY KEY(exchange,symbol)
                                );
drop table if exists trigger;
create table if not exists trigger( seqnum integer PRIMARY KEY,
                                    symbol text NOT NULL,
                                    trade text NOT NULL,
                                    rate real, 
                                    count integer DEFAULT 0,
                                    updated_at TIMESTAMP DEFAULT(DATETIME('now','localtime'))
                                );
drop table if exists ratelogs;
create table if not exists ratelogs( seqnum integer PRIMARY KEY AUTOINCREMENT,
                                    exchange text,
                                    symbol text NOT NULL,
                                    rate real, 
                                    inserted_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    time_epoch integer
                                );
