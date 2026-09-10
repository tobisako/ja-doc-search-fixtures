import { Injectable, Logger, NotFoundException, OnModuleInit } from '@nestjs/common';
import { readFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

/** expected.json の1件 */
export interface Fixture {
  file: string;
  group: string;
  why: string;
  expect: {
    must_find?: string[];
    must_keep?: string[];
    must_not_contain_cp?: string[];
    known_unfixable_cp?: string[];
    must_fail?: boolean;
  };
}

const HERE = dirname(fileURLToPath(import.meta.url));
/** dist/fixtures から見たリポジトリ直下 */
const REPO_ROOT = join(HERE, '..', '..', '..');

/**
 * 20本のテストデータと、その採点基準を持つ。
 *
 * 【なぜサービスなのか】expected.json はプロセス起動中に変わらない。
 * OnModuleInit で1度だけ読み、以後は配ることに徹する。
 * 読み込みに失敗したら**起動時に落とす**。採点のたびに落ちるより分かりやすい。
 */
@Injectable()
export class FixturesService implements OnModuleInit {
  private readonly logger = new Logger(FixturesService.name);
  private fixtures: Fixture[] = [];

  async onModuleInit(): Promise<void> {
    const path = join(REPO_ROOT, 'expected.json');
    const raw = await readFile(path, 'utf-8');
    this.fixtures = (JSON.parse(raw) as { fixtures: Fixture[] }).fixtures;
    const groups = [...new Set(this.fixtures.map((f) => f.group))];
    this.logger.log(`テストデータ ${this.fixtures.length}本を読み込みました（${groups.join(' / ')}）`);
  }

  all(): Fixture[] {
    return this.fixtures;
  }

  byGroup(group?: string): Fixture[] {
    return group ? this.fixtures.filter((f) => f.group === group) : this.fixtures;
  }

  find(file: string): Fixture {
    const hit = this.fixtures.find((f) => f.file === file);
    if (!hit) throw new NotFoundException(`そのテストデータはありません: ${file}`);
    return hit;
  }

  /** テストデータの実体。抽出器に渡してもらうために配る */
  async bytes(file: string): Promise<Buffer> {
    this.find(file); // 一覧に無い名前でファイルを読ませない
    return readFile(join(REPO_ROOT, 'fixtures', file));
  }

  groups(): { group: string; count: number }[] {
    const map = new Map<string, number>();
    for (const f of this.fixtures) map.set(f.group, (map.get(f.group) ?? 0) + 1);
    return [...map].map(([group, count]) => ({ group, count }));
  }
}
