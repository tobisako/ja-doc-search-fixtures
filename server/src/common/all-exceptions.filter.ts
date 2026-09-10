import { ArgumentsHost, Catch, ExceptionFilter, HttpException, HttpStatus, Logger } from '@nestjs/common';
import type { Response } from 'express';

/**
 * 例外の形をひとつに揃える。
 *
 * **利用者に返す形を1箇所で決める。** 各ハンドラが独自の形で失敗を返すと、
 * 呼び出し側が分岐を書き分けることになる。
 */
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  private readonly logger = new Logger('Exception');

  catch(exception: unknown, host: ArgumentsHost): void {
    const res = host.switchToHttp().getResponse<Response>();
    const req = host.switchToHttp().getRequest<{ method: string; url: string }>();

    const status = exception instanceof HttpException ? exception.getStatus() : HttpStatus.INTERNAL_SERVER_ERROR;
    const body = exception instanceof HttpException ? exception.getResponse() : String(exception);

    this.logger.error(`${req.method} ${req.url} → ${status}: ${JSON.stringify(body)}`);
    res.status(status).json({ error: { status, message: body, path: req.url, at: new Date().toISOString() } });
  }
}
