drop table if exists balance;
create table if not exists balance( exchange text NOT NULL,
                                    symbol text NOT NULL,
                                    amount real,
                                    rate real, 
                                    jpy real, 
                                    updated_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    PRIMARY KEY(exchange,symbol)
                                );