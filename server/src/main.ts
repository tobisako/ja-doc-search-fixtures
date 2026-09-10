import 'reflect-metadata';
import { Logger, ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import type { NestExpressApplication } from '@nestjs/platform-express';
import { AppModule } from './app.module.js';
import { AllExceptionsFilter } from './common/all-exceptions.filter.js';
import { TimingInterceptor } from './common/timing.interceptor.js';

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create<NestExpressApplication>(AppModule);

  // 本文の上限。Guard で合計を見張るのではなく、**受け口で決める**
  app.useBodyParser('json', { limit: '16mb' });

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,            // DTO に無い項目は落とす
      forbidNonWhitelisted: true, // 知らない項目が来たら断る（綴り間違いを黙って無視しない）
      transform: true,
    }),
  );
  app.useGlobalFilters(new AllExceptionsFilter());
  app.useGlobalInterceptors(new TimingInterceptor());
  app.enableCors();

  const port = Number(process.env.PORT ?? 3100);
  await app.listen(port);
  new Logger('Bootstrap').log(`検査API: http://localhost:${port}  （CLI と同じ採点基準を使います）`);
}

await bootstrap();
