# Custom App - CCAvenue Integration

This is a custom ERPNext app that integrates CCAvenue payment gateway with ERPNext v15 webshop.

## Features

- Complete CCAvenue payment integration
- Secure AES encryption/decryption
- Payment verification and callback handling
- Automatic payment entry creation
- Support for test and live modes
- Comprehensive error handling
- Customer billing and shipping address integration

## Installation

1. Install the app:
   ```bash
   bench get-app custom_app
   bench install-app custom_app
   ```

2. Install dependencies:
   ```bash
   pip install pycryptodome
   ```

3. Run migrations:
   ```bash
   bench migrate
   ```

4. Configure CCAvenue Settings:
   - Go to CCAvenue Settings
   - Enter your Merchant ID, Access Code, and Working Key
   - Enable the gateway
   - Set test mode if needed

5. Add to E Commerce Settings:
   - Go to E Commerce Settings
   - Add CCAvenue as a payment method

## Configuration

### CCAvenue Settings
- **Merchant ID**: Your CCAvenue merchant ID
- **Access Code**: Your CCAvenue access code  
- **Working Key**: Your CCAvenue working key
- **Test Mode**: Enable for testing
- **Supported Currencies**: Comma-separated list of currencies

### Payment Flow
1. Customer adds items to cart
2. Proceeds to checkout
3. Selects CCAvenue payment
4. Redirected to CCAvenue payment page
5. Completes payment
6. Redirected back with payment status
7. Payment entry created automatically

## Security

- All sensitive data is encrypted using AES encryption
- Payment responses are verified for authenticity
- Secure callback handling prevents tampering

## License

MIT
