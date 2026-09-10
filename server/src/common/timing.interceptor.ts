import { CallHandler, ExecutionContext, Injectable, Logger, NestInterceptor } from '@nestjs/common';
import { Observable, tap } from 'rxjs';

/**
 * 所要時間を測って残す。
 *
 * **横断的関心事をハンドラから追い出すための層。**
 * 採点そのもの（CheckService）は時間の計測を知らない。
 */
@Injectable()
export class TimingInterceptor implements NestInterceptor {
  private readonly logger = new Logger('Timing');

  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    const req = context.switchToHttp().getRequest<{ method: string; url: string }>();
    const startedAt = Date.now();
    return next.handle().pipe(
      tap(() => this.logger.log(`${req.method} ${req.url} — ${Date.now() - startedAt}ms`)),
    );
  }
}
