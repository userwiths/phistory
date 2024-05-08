class Existance:
    @staticmethod
    def exists(table: str, arguments: dict, cursor) -> bool:
        query = f"SELECT * FROM {table} WHERE "
        for key, value in arguments.items():
            query += f"{key} = % AND "
        query = query[:-4]
        cursor.execute(query, list(arguments.values()))
        return cursor.fetchone() is not None