import { Module } from '@nestjs/common';
import { FixturesService } from './fixtures/fixtures.service.js';
import { CheckService } from './check/check.service.js';
import { CheckController } from './check/check.controller.js';

/**
 * 検査APIサーバ。
 *
 * 【CLIとの関係】**CLIが主。** こちらは、抽出結果を受け取って採点するだけの入口。
 * CLI は抽出ツールを自分で実行するが、こちらは実行しない（送られた結果を見るだけ）。
 *
 * **採点そのもの（CheckService）は HTTP を知らない。** CLI (`check.py`) と
 * 同じ4種類の判定を、同じ `expected.json` で行う。
 * **両者の結果が一致することが、機能を足すことより優先。**
 */
@Module({
  controllers: [CheckController],
  providers: [FixturesService, CheckService],
})
export class AppModule {}
