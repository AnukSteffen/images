package com.wu.personai.database

import androidx.room.Database
import androidx.room.RoomDatabase
import com.wu.personai.dao.ChatDao
import com.wu.personai.entity.ChatEntity

@Database(entities = [ChatEntity::class], version = 1)
abstract class AppDatabase : RoomDatabase(){
    abstract fun chatDao() : ChatDao
}