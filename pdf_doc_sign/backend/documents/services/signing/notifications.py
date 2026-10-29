"""
SigningNotificationService — Handles email triggers after signing events.
All email failures are caught and logged; they never break the signing flow.
"""
import logging

logger = logging.getLogger('documents.signing.notifications')


class SigningNotificationService:

    @staticmethod
    def on_signer_completed(signer):
        """
        Notify the document owner that a signer has completed.
        Called after each individual signature.
        """
        try:
            from documents.emails.notifications import notify_sender_signer_completed
            notify_sender_signer_completed(signer.document, signer)
        except Exception as e:
            logger.error(f'[NOTIFY] Failed to notify sender for signer {signer.signer_email}: {e}')

    @staticmethod
    def on_document_completed(document):
        """
        Notify all parties (sender + signers) that the document is fully signed.
        Called once when the last signer completes.
        """
        try:
            from documents.emails.notifications import notify_all_document_completed
            notify_all_document_completed(document)
        except Exception as e:
            logger.error(f'[NOTIFY] Failed to send completion emails for doc {document.id}: {e}')
