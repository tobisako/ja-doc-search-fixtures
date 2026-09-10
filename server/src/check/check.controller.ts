import { BadRequestException, Body, Controller, Get, Param, Post, Query, Res } from '@nestjs/common';
import type { Response } from 'express';
import { FixturesService } from '../fixtures/fixtures.service.js';
import { CheckService, type Verdict } from './check.service.js';
import { BatchDto, SubmissionDto } from './check.dto.js';

/** 採点仕様の版。**結果に必ず添える。** 版が違えば合否が変わりうるため */
export const SPEC_VERSION = '1';

@Controller()
export class CheckController {
  constructor(
    private readonly fixtures: FixturesService,
    private readonly check: CheckService,
  ) {}

  /** 20本の一覧と、それぞれ何を証明するか */
  @Get('fixtures')
  list(@Query('group') group?: string) {
    const items = this.fixtures.byGroup(group);
    if (group && items.length === 0) {
      throw new BadRequestException(
        `そのグループはありません: ${group}（ある: ${this.fixtures.groups().map((g) => g.group).join(' / ')}）`,
      );
    }
    return { specVersion: SPEC_VERSION, total: items.length, groups: this.fixtures.groups(), fixtures: items };
  }

  /** テストデータの実体。抽出器に読ませるために配る */
  @Get('fixtures/:file/raw')
  async raw(@Param('file') file: string, @Res() res: Response): Promise<void> {
    const bytes = await this.fixtures.bytes(file);
    res.setHeader('content-type', 'application/octet-stream');
    res.setHeader('content-disposition', `attachment; filename*=UTF-8''${encodeURIComponent(file)}`);
    res.send(bytes);
  }

  /** 1件を採点する */
  @Post('check')
  one(@Body() dto: SubmissionDto) {
    return { specVersion: SPEC_VERSION, verdict: this.judge(dto) };
  }

  /**
   * まとめて採点する。
   *
   * **出していないものを「合格」にしない。** 20本のうち送られなかったものは
   * `notSubmitted` として名前を返す。黙って母数から外すと、
   * 「20本中20本合格」に見えて実は3本しか出していない、が起きる。
   */
  @Post('check/batch')
  batch(@Body() dto: BatchDto) {
    const seen = new Set<string>();
    for (const s of dto.submissions) {
      if (seen.has(s.file)) throw new BadRequestException(`同じテストデータが2回送られています: ${s.file}`);
      seen.add(s.file);
    }

    const verdicts = dto.submissions.map((s) => this.judge(s));
    const notSubmitted = this.fixtures.all().map((f) => f.file).filter((f) => !seen.has(f));

    return {
      specVersion: SPEC_VERSION,
      label: dto.label,
      ...this.check.summarize(verdicts),
      notSubmitted,
      note:
        'failed は「送り手が抽出できなかったと申告した」という意味です。' +
        'このサーバが抽出を試したわけではありません。',
    };
  }

  private judge(dto: SubmissionDto): Verdict {
    // text と failed の同時指定は受けない。どちらとも取れる入力を通さない
    if (dto.failed === true && dto.text !== undefined) {
      throw new BadRequestException(
        `${dto.file}: text と failed:true は同時に指定できません（抽出できたのか、できなかったのかが決まりません）`,
      );
    }
    if (dto.failed !== true && dto.text === undefined) {
      throw new BadRequestException(
        `${dto.file}: text か failed:true のどちらかが要ります（空文字を成功として受け取らないため）`,
      );
    }
    return this.check.judge(dto.file, dto.text ?? null, dto.failed === true);
  }
}
