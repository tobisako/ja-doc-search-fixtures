import { describe, it, expect, beforeEach } from 'vitest';
import { CheckService } from './check.service.js';
import type { FixturesService, Fixture } from '../fixtures/fixtures.service.js';

/** FixturesService の代わり。DIで差し替えられるので、ファイルを読まずに試せる */
function stub(fx: Fixture): FixturesService {
  return { find: () => fx } as unknown as FixturesService;
}

describe('CheckService — 4種類の判定', () => {
  it('引けるべき語が引けなければ落とす。NFKCで見つかるなら正規化漏れと言う', () => {
    const s = new CheckService(stub({ file: 'a.pdf', group: 'kangxi', why: '',
      expect: { must_find: ['人事'] } }));
    const v = s.judge('a.pdf', '⼈事評価制度', false);   // U+2F08
    expect(v.passed).toBe(false);
    expect(v.problems[0].type).toBe('not_found');
    expect(v.problems[0].nfkcWouldFix).toBe(true);
  });

  it('潰してはいけない文字列が消えていたら落とす（NFKCの掛けすぎ）', () => {
    const s = new CheckService(stub({ file: 'a.pdf', group: 'zenkaku', why: '',
      expect: { must_keep: ['（消費税別）'] } }));
    expect(s.judge('a.pdf', '月額 1,000円(消費税別)', false).problems[0].type).toBe('not_kept');
    expect(s.judge('a.pdf', '月額 1,000円（消費税別）', false).passed).toBe(true);
  });

  it('直し残しのコードポイントを名指しする', () => {
    const s = new CheckService(stub({ file: 'a.pdf', group: 'kangxi', why: '',
      expect: { must_not_contain_cp: ['2F08'] } }));
    const v = s.judge('a.pdf', '⼈事', false);
    expect(v.problems[0].cp).toBe('2F08');
  });

  /** **一番大事な判定。** 空文字を成功として受け取らない */
  it('読めないと言うべきものを、空文字で成功にしたら落とす', () => {
    const s = new CheckService(stub({ file: 'a.pdf', group: 'no-text', why: '',
      expect: { must_fail: true } }));
    expect(s.judge('a.pdf', '', false).problems[0].type).toBe('should_have_failed');
    expect(s.judge('a.pdf', '', false).problems[0].message).toContain('空文字を成功として返している');
    expect(s.judge('a.pdf', null, true).passed).toBe(true);   // 失敗と言えていれば合格
  });

  it('読めるはずのものを落としたら、そう言う', () => {
    const s = new CheckService(stub({ file: 'a.pdf', group: 'kangxi', why: '',
      expect: { must_find: ['人事'] } }));
    expect(s.judge('a.pdf', null, true).problems[0].type).toBe('should_have_succeeded');
  });
});
