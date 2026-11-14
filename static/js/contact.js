const form = document.querySelector('[data-contact-form]');
const FORMSUBMIT_ENDPOINT = 'https://formsubmit.co/ajax/amyhamlyn@live.com';

if (form) {
  const submitButton = form.querySelector('button[type="submit"]');
  const statusMessage = document.querySelector('#contact-status');
  const submitLabel = submitButton.textContent;
  let isSubmitting = false;

  function showStatus(message, state) {
    statusMessage.textContent = message;
    statusMessage.dataset.state = state;
    statusMessage.hidden = false;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (isSubmitting || !form.reportValidity()) return;

    isSubmitting = true;
    submitButton.disabled = true;
    submitButton.setAttribute('aria-busy', 'true');
    submitButton.textContent = 'Sending...';
    showStatus('Sending your enquiry...', 'loading');

    try {
      const formData = new FormData(form);
      const payload = Object.fromEntries(formData.entries());
      payload._replyto = payload.email;

      const response = await fetch(FORMSUBMIT_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(payload),
      });
      const result = await response.json().catch(() => ({}));

      const submissionSucceeded = result.success === true || result.success === 'true';
      if (!response.ok || !submissionSucceeded) {
        throw new Error(result.message || result.error || 'We could not send your enquiry. Please try again.');
      }

      form.reset();
      showStatus(result.message || 'Thank you. Your enquiry has been sent.', 'success');
    } catch (error) {
      showStatus(error.message || 'We could not send your enquiry. Please try again.', 'error');
    } finally {
      isSubmitting = false;
      submitButton.disabled = false;
      submitButton.removeAttribute('aria-busy');
      submitButton.textContent = submitLabel;
    }
  });
}