import { Type } from 'class-transformer';
import { ArrayMaxSize, IsArray, IsBoolean, IsOptional, IsString, MaxLength, ValidateNested } from 'class-validator';

/**
 * 1件分の採点依頼。
 *
 * 【要点】`text` は任意で `failed` が真偽値。
 * **「抽出できなかった」を空文字ではなく `failed: true` で表す**ための形。
 * ここを曖昧にすると、このAPI自身が「黙って空を返す」のと同じ罪を犯す。
 */
export class SubmissionDto {
  // 【要点】text と failed は**同時に指定させない**。
  // 「空文字だが成功」と「抽出できなかった」が混ざると、このAPI自身が
  // 採点対象と同じ罪（黙って空を返す）を犯すことになる。検証で弾く。
  @IsString()
  @MaxLength(200)
  file!: string;

  /** 抽出できたテキスト。抽出に失敗したなら省略する */
  @IsOptional()
  @IsString()
  @MaxLength(2_000_000)
  text?: string;

  /** 抽出できなかったか。テキスト層が無い等 */
  @IsOptional()
  @IsBoolean()
  failed?: boolean;
}

export class BatchDto {
  @IsArray()
  @ArrayMaxSize(200)
  @ValidateNested({ each: true })
  @Type(() => SubmissionDto)
  submissions!: SubmissionDto[];

  /** 誰の抽出器かを結果に添える（任意）。ログの読み分けに使う */
  @IsOptional()
  @IsString()
  @MaxLength(80)
  label?: string;
}
