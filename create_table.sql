--drop table if exists balance;
create table if not exists balance( exchange text NOT NULL,
                                    symbol text NOT NULL,
                                    amount real,
                                    rate real, 
                                    jpy real, 
                                    updated_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    PRIMARY KEY(exchange,symbol)
                                );
--
drop table if exists trigger;
create table if not exists trigger( seqnum integer PRIMARY KEY,
                                    symbol text NOT NULL,
                                    trade text NOT NULL,
                                    exectype text default 'MARKET',
                                    exchange text,
                                    rate real, 
                                    method text default 'IM',
                                    amount real default 0.0,
                                    count integer DEFAULT 0,
                                    continuing int default 0,
                                    histgram real default 0.0,
                                    pass int default 0,
                                    updated_at TIMESTAMP DEFAULT(DATETIME('now','localtime'))
                                );
--
--drop table if exists orders;
create table if not exists orders(  id integer NOT NULL,
                                    exchange text NOT NULL,
                                    pair text NOT NULL,
                                    order_side text NOT NULL, 
                                    order_type text, 
                                    rate real NOT NULL, 
                                    amount real NOT NULL,
                                    order_state integer DEFAULT 0, 
                                    created_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    PRIMARY KEY(id, exchange)
                                );
--
--drop table if exists ratelogs;
create table if not exists ratelogs( seqnum integer PRIMARY KEY AUTOINCREMENT,
                                    exchange text,
                                    symbol text NOT NULL,
                                    rate real, 
                                    inserted_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    time_epoch integer
                                );
