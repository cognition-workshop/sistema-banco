from django.shortcuts import redirect


def ensure_user_bank_account(backend, user, *args, **kwargs):
    """
    Custom pipeline function to ensure OAuth users have a bank account.
    If the user doesn't have a bank account, redirect to account setup page.
    This function is placed at the end of the pipeline, so the user is fully authenticated.
    """
    if user and not hasattr(user, 'account'):
        return redirect('accounts:oauth_account_setup')
    return {}
