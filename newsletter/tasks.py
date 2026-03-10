"""
Celery tasks for newsletter emails.
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def _build_html_email(subject, message):
    """Wrap plain-text message in a clean HTML email template.
    Preserves line breaks exactly as written in Django Admin."""
    import html as html_lib
    # Escape any HTML special chars, then convert newlines to <br>
    body_html = html_lib.escape(message).replace('\n', '<br>\n')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_lib.escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:30px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <!-- Header -->
          <tr>
            <td style="background:#006E3E;padding:24px 32px;">
              <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:bold;">
                🕌 Salahtime Newsletter
              </h1>
            </td>
          </tr>
          <!-- Subject heading -->
          <tr>
            <td style="padding:28px 32px 0 32px;">
              <h2 style="margin:0;color:#006E3E;font-size:20px;font-weight:bold;">
                {html_lib.escape(subject)}
              </h2>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:16px 32px 32px 32px;color:#333333;font-size:16px;line-height:1.7;">
              {body_html}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background:#f9f9f9;padding:20px 32px;border-top:1px solid #e5e5e5;font-size:13px;color:#888888;text-align:center;">
              You received this because you subscribed to the Salahtime newsletter.<br>
              To unsubscribe, reply with <strong>STOP</strong> or visit our website.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


@shared_task(bind=True, max_retries=3)
def send_newsletter_email(self, subscription_id, campaign_id):
    """
    Send a single newsletter email to one subscriber.
    Called per-subscriber from send_newsletter_campaign.
    """
    from newsletter.models import NewsletterSubscription, NewsletterCampaign, NewsletterLog
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings

    try:
        subscription = NewsletterSubscription.objects.get(id=subscription_id)
        campaign = NewsletterCampaign.objects.get(id=campaign_id)

        log = NewsletterLog.objects.create(
            subscription=subscription,
            subject=campaign.subject,
            message=campaign.message,
            status='draft',
        )

        plain_text = (
            campaign.message
            + "\n\n---\n"
            "You received this because you subscribed to Salahtime newsletter.\n"
            "To unsubscribe, reply with STOP or visit our website."
        )
        html_content = _build_html_email(campaign.subject, campaign.message)

        try:
            msg = EmailMultiAlternatives(
                subject=campaign.subject,
                body=plain_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[subscription.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

            log.status = 'sent'
            log.sent_at = timezone.now()
            logger.info(f"[Newsletter] Sent '{campaign.subject}' to {subscription.email}")
        except Exception as mail_exc:
            log.status = 'failed'
            log.error_message = str(mail_exc)
            logger.error(f"[Newsletter] Failed to send to {subscription.email}: {mail_exc}")
        finally:
            log.save()

        return {'status': log.status, 'email': subscription.email}

    except (NewsletterSubscription.DoesNotExist, NewsletterCampaign.DoesNotExist) as e:
        logger.error(f"[Newsletter] Object not found: {e}")
        return {'status': 'error', 'message': str(e)}
    except Exception as exc:
        logger.error(f"[Newsletter] Unexpected error: {exc}")
        self.retry(exc=exc, countdown=60)


@shared_task(bind=True)
def send_newsletter_campaign(self, campaign_id):
    """
    Dispatch newsletter campaign to all active subscribers.
    Called from Django admin action.
    """
    from newsletter.models import NewsletterCampaign, NewsletterSubscription

    try:
        campaign = NewsletterCampaign.objects.get(id=campaign_id)

        if campaign.status == 'sent':
            logger.warning(f"[Newsletter] Campaign {campaign_id} already sent, skipping.")
            return {'status': 'already_sent'}

        campaign.status = 'sending'
        campaign.save(update_fields=['status'])

        subscribers = NewsletterSubscription.objects.filter(is_active=True)
        count = subscribers.count()

        if count == 0:
            campaign.status = 'sent'
            campaign.sent_at = timezone.now()
            campaign.total_sent = 0
            campaign.save(update_fields=['status', 'sent_at', 'total_sent'])
            return {'status': 'success', 'queued': 0, 'reason': 'no_active_subscribers'}

        for subscription in subscribers:
            send_newsletter_email.apply(args=[str(subscription.id), str(campaign_id)])

        campaign.status = 'sent'
        campaign.sent_at = timezone.now()
        campaign.total_sent = count
        campaign.save(update_fields=['status', 'sent_at', 'total_sent'])

        logger.info(f"[Newsletter] Campaign '{campaign.subject}' dispatched to {count} subscribers.")
        return {'status': 'success', 'queued': count}

    except NewsletterCampaign.DoesNotExist:
        logger.error(f"[Newsletter] Campaign {campaign_id} not found")
        return {'status': 'error', 'message': 'Campaign not found'}
    except Exception as exc:
        logger.error(f"[Newsletter] Campaign dispatch error: {exc}")
        raise
