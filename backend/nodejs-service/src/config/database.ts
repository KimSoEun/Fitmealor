import { DataSource } from 'typeorm';
import { User } from '../entities/User';
import { HealthProfile } from '../entities/HealthProfile';
import { Allergy } from '../entities/Allergy';
import { Meal } from '../entities/Meal';
import { Favorite } from '../entities/Favorite';
import { MealLog } from '../entities/MealLog';

export const AppDataSource = new DataSource({
  type: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  username: process.env.DB_USER || 'fitmealor_user',
  password: process.env.DB_PASSWORD || 'fitmealor_pass',
  database: process.env.DB_NAME || 'fitmealor',
  synchronize: false, // Use migrations in production
  logging: process.env.NODE_ENV === 'development',
  entities: [User, HealthProfile, Allergy, Meal, Favorite, MealLog],
  migrations: ['src/migrations/*.ts'],
  subscribers: [],
});
