import aiosqlite
import datetime
import calendar


def datetime_to_int(x):
    return calendar.timegm(x.utctimetuple())


class DBInteractor:
    db = None

    @classmethod
    async def create(cls):
        self = DBInteractor()
        self.db = await aiosqlite.connect("database.db")
        return self

    async def create_tables_if_not_exists(self):
        await self.db.execute("""CREATE TABLE IF NOT EXISTS "StrongNotifications" (
                                    "user_id" INTEGER,
                                    "description" TEXT,
                                    "date_time" INTEGER
                );""")
        await self.db.execute("""CREATE TABLE IF NOT EXISTS "WeakNotifications" (
                                            "user_id" INTEGER,
                                            "description" TEXT,
                                            "date_time" INTEGER
                        );""")
        await self.db.commit()

    async def insert_into_strong(self, user_id, desc, time_strong):
        await self.db.execute(
            f"""INSERT INTO StrongNotifications VALUES {(user_id, desc, datetime_to_int(time_strong))}""")
        await self.db.commit()

    async def insert_into_weak(self, user_id, desc, time_weak):
        await self.db.execute(
            f"""INSERT INTO WeakNotifications VALUES {(user_id, desc, datetime_to_int(time_weak))}""")
        await self.db.commit()

    async def create_deadline(self, user_id: int, desc: str, time: datetime.datetime) -> None:
        """
        Add notifications for deadline into database
        :param user_id: deadline user id
        :param desc: deadline text
        :param time: deadline time
        """
        time_strong = time - datetime.timedelta(hours=2)
        time_weak = time - datetime.timedelta(days=3)
        await self.insert_into_strong(user_id, desc, time_strong)
        await self.insert_into_weak(user_id, desc, time_weak)

    async def deadlines_list(self, user_id: int) -> list:
        """
        Get list of active deadlines for user
        :param user_id: user id
        :return list of tuples (desc, time) of types (str, datetime)
        """
        cur = await self.db.execute(f"""SELECT * from StrongNotifications WHERE user_id={user_id}""")
        ans = [(i[1], datetime.datetime.fromtimestamp(i[2] + 3600 * 2)) for i in
               await cur.fetchall()]  # 2022-12-09 21:59:00
        await cur.close()
        return ans

    async def get_overdue(self, table_name, time=datetime.datetime.now()):
        return await self.db.execute(
            f"""SELECT * from {table_name} WHERE date_time<{datetime_to_int(time)}""")

    async def get_overdue_weak(self):
        cur = await self.get_overdue("WeakNotifications")
        ans = [(i[0], i[1], datetime.datetime.fromtimestamp(i[2])) for i in
               await cur.fetchall()]  # 2022-12-09 21:59:00
        await cur.close()
        return ans

    async def get_overdue_strong(self):
        cur = await self.get_overdue("StrongNotifications")
        ans = [(i[0], i[1], datetime.datetime.fromtimestamp(i[2])) for i in
               await cur.fetchall()]  # 2022-12-09 21:59:00
        await cur.close()
        return ans

    async def delete_overdue(self):
        for table_name in ("StrongNotifications", "WeakNotifications"):
            await self.db.execute(
                f"""DELETE from {table_name} WHERE date_time<{datetime_to_int(datetime.datetime.now())}""")
        await self.db.commit()

    async def shift_all_until(self, time: datetime.datetime) -> None:
        """
        Shift  all weak notifications until time 1 day forward
        :param time: latest notification time
        """
        await self.db.execute(
            f"""UPDATE WeakNotifications set date_time=date_time+86400 where date_time<{datetime_to_int(time)}""")
        await self.db.commit()



