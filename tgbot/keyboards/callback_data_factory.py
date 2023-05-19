from aiogram.utils.callback_data import CallbackData

vpn_callback = CallbackData('vpn', 'action_type', 'server')
vpn_buy_callback = CallbackData('buy', 'days', 'amount', 'type')
vpn_p2p_callback = CallbackData('p2p', 'action_type', 'server')
vpn_p2p_claim_callback = CallbackData('p2p', 'action_type', 'server', 'label')
vpn_keys_callback = CallbackData('vpn', 'action_type', 'key')
trial_callback = CallbackData('trial', 'action_type', 'server', 'label')
