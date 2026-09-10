import { Injectable } from '@nestjs/common';
import { FixturesService, type Fixture } from '../fixtures/fixtures.service.js';

/** 1件の指摘 */
export interface Problem {
  type: 'not_found' | 'not_kept' | 'unnormalized_cp' | 'should_have_failed' | 'should_have_succeeded';
  message: string;
  value?: string;
  cp?: string;
  /** NFKC を掛ければ見つかるか。true なら正規化漏れと確定する */
  nfkcWouldFix?: boolean;
}

export interface Verdict {
  file: string;
  group: string;
  why: string;
  passed: boolean;
  problems: Problem[];
}

export interface Report {
  total: number;
  passed: number;
  failed: number;
  byGroup: Record<string, { passed: number; failed: number }>;
  verdicts: Verdict[];
}

/**
 * 採点そのもの。**HTTPもWebSocketも知らない。**
 *
 * 判定は4種類だけ。
 *   must_find            引けるべき語が引けるか
 *   must_keep            潰していないか（NFKCを掛けすぎていないか）
 *   must_not_contain_cp  直し残しが無いか
 *   must_fail            黙って空を返していないか
 */
@Injectable()
export class CheckService {
  constructor(private readonly fixtures: FixturesService) {}

  judge(file: string, text: string | null, extractionFailed: boolean): Verdict {
    const fx = this.fixtures.find(file);
    const problems = this.problemsOf(fx, text ?? '', extractionFailed);
    return { file: fx.file, group: fx.group, why: fx.why, passed: problems.length === 0, problems };
  }

  summarize(verdicts: Verdict[]): Report {
    const byGroup: Record<string, { passed: number; failed: number }> = {};
    for (const v of verdicts) {
      byGroup[v.group] ??= { passed: 0, failed: 0 };
      byGroup[v.group][v.passed ? 'passed' : 'failed']++;
    }
    return {
      total: verdicts.length,
      passed: verdicts.filter((v) => v.passed).length,
      failed: verdicts.filter((v) => !v.passed).length,
      byGroup,
      verdicts,
    };
  }

  private problemsOf(fx: Fixture, text: string, failed: boolean): Problem[] {
    const e = fx.expect;
    const out: Problem[] = [];

    // 「読めない」と言えることが正解の問題
    if (e.must_fail) {
      if (!failed) {
        out.push({
          type: 'should_have_failed',
          message:
            text.trim().length === 0
              ? '抽出できないはずが、成功して0文字返った（空文字を成功として返している）'
              : `抽出できないはずが、成功して${text.trim().length}文字返った`,
        });
      }
      return out;
    }

    if (failed) {
      out.push({ type: 'should_have_succeeded', message: '抽出できるはずが、失敗した' });
      return out;
    }

    for (const w of e.must_find ?? []) {
      if (text.includes(w)) continue;
      // 【要点】見つからない理由まで言う。NFKCで見つかるなら正規化漏れと確定する
      const wouldFix = text.normalize('NFKC').includes(w);
      out.push({
        type: 'not_found',
        value: w,
        nfkcWouldFix: wouldFix,
        message: `「${w}」が見つからない${wouldFix ? '（NFKC を掛ければ見つかる＝正規化されていない）' : ''}`,
      });
    }

    for (const w of e.must_keep ?? []) {
      if (text.includes(w)) continue;
      out.push({
        type: 'not_kept',
        value: w,
        message: `「${w}」が保たれていない（NFKC で潰していないか）`,
      });
    }

    for (const hex of e.must_not_contain_cp ?? []) {
      const ch = String.fromCodePoint(parseInt(hex, 16));
      if (!text.includes(ch)) continue;
      out.push({
        type: 'unnormalized_cp',
        cp: hex,
        value: ch,
        message: `U+${hex} 「${ch}」がそのまま残っている（正規化されていない）`,
      });
    }

    return out;
  }
}
