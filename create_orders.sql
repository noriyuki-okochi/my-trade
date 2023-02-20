drop table if exists orders;
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
