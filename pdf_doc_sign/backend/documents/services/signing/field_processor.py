"""
FieldProcessor — Handles filling signature/name/date fields for a signer.
Pure data logic, no emails, no status checks.
"""
import logging
from django.utils import timezone

logger = logging.getLogger('documents.signing.fields')


class FieldProcessor:

    @staticmethod
    def fill_signer_fields(signer, signature_image, filled_values=None):
        """
        Fill all fields assigned to this signer with the appropriate values.
        - SIGNATURE / INITIALS → signature image
        - NAME → signer-provided override (if any) or signer.signer_name
        - DATE → signer-provided override (if any) or current date
        - TEXT → signer-provided value (if any); empty fields are left blank

        Args:
            filled_values: optional dict of { field_id_str: value_str }
                from the signer. Only applied for non-image field types.
        """
        from documents.models import SignatureField

        now = timezone.now()
        overrides = {str(k): v for k, v in (filled_values or {}).items()}

        # 1. Image fields (SIGNATURE, INITIALS) — each needs its own copy
        for field_type in ('SIGNATURE', 'INITIALS'):
            fields = SignatureField.objects.filter(
                document=signer.document,
                signer_index=signer.signing_order,
                field_type=field_type,
            )
            for sf in fields:
                sf.filled_signature = signature_image
                sf.filled_at = now
                sf.save(update_fields=['filled_signature', 'filled_at'])

        # 2. NAME fields — signer override takes precedence over signer_name
        for nf in SignatureField.objects.filter(
            document=signer.document,
            signer_index=signer.signing_order,
            field_type='NAME',
        ):
            override = overrides.get(str(nf.id), '').strip()
            nf.filled_value = override or signer.signer_name
            nf.filled_at = now
            nf.save(update_fields=['filled_value', 'filled_at'])

        # 3. DATE fields — signer override takes precedence over today's date
        for df in SignatureField.objects.filter(
            document=signer.document,
            signer_index=signer.signing_order,
            field_type='DATE',
        ):
            override = overrides.get(str(df.id), '').strip()
            df.filled_value = override or now.strftime('%d %b %Y')
            df.filled_at = now
            df.save(update_fields=['filled_value', 'filled_at'])

        # 4. TEXT fields — only fill if the signer actually provided a value.
        # Required-field validation happens client-side; if we reach here
        # an unfilled TEXT field just stays blank in the final PDF.
        for tf in SignatureField.objects.filter(
            document=signer.document,
            signer_index=signer.signing_order,
            field_type='TEXT',
        ):
            value = overrides.get(str(tf.id), '').strip()
            if value:
                tf.filled_value = value
                tf.filled_at = now
                tf.save(update_fields=['filled_value', 'filled_at'])

        # 5. CHECKBOX fields — store 'true' if the signer ticked, 'false' if
        # they explicitly left it unticked, blank if they never touched it
        # (the frontend sends 'true'/'false' for any checkbox the signer
        # interacted with; required checkboxes that must be ticked are
        # enforced client-side via allFieldsFilled).
        for cb in SignatureField.objects.filter(
            document=signer.document,
            signer_index=signer.signing_order,
            field_type='CHECKBOX',
        ):
            raw = overrides.get(str(cb.id), '').strip().lower()
            if raw in ('true', '1', 'yes', 'on', 'checked'):
                cb.filled_value = 'true'
                cb.filled_at = now
                cb.save(update_fields=['filled_value', 'filled_at'])
            elif raw in ('false', '0', 'no', 'off', 'unchecked'):
                cb.filled_value = 'false'
                cb.filled_at = now
                cb.save(update_fields=['filled_value', 'filled_at'])
            # else: signer never touched it — leave filled_value blank so
            # the PDF generator can distinguish "skipped" from "unticked"

        logger.debug(f'Filled fields for signer {signer.signer_name} on doc {signer.document.id}')
