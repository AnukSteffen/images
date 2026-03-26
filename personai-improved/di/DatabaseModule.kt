package com.wu.personai.di;

import android.content.Context;
import androidx.room.Room;
import com.wu.personai.dao.ChatDao;
import com.wu.personai.database.AppDatabase;
import com.wu.personai.net.CloudEngine;
import com.wu.personai.local.LLMEngine;
import com.wu.personai.repository.LocalLLMEngine;
import dagger.Module;
import dagger.Provides;
import dagger.hilt.InstallIn;
import dagger.hilt.android.qualifiers.ApplicationContext;
import dagger.hilt.components.SingletonComponent;
import javax.inject.Singleton;

@Module
@InstallIn(SingletonComponent.class)
object DatabaseModule {
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder(context, AppDatabase.class.java, "person_ai_db").build();
    }

    @Provides
    fun provideChatDao(database: AppDatabase): ChatDao {
        return database.chatDao();
    }

    @Provides
    @Singleton
    fun provideCloudEngine(): CloudEngine {
        return CloudEngine();
    }

    @Provides
    @Singleton
    fun provideLocalLLMEngine(@ApplicationContext context: Context): LLMEngine {
        return LocalLLMEngine(context);
    }
}