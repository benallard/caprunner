package javatest;

import javacard.framework.Applet;
import javacard.framework.ISO7816;
import javacard.framework.Util;
import javacard.framework.ISOException;
import javacard.framework.APDU;
import javacard.framework.JCSystem;

/**
 * Copyright Jean-Pierre Szikora and Philippe Teuwen - 2011                                     *
 * Cette création est mise à disposition selon le Contrat Attribution-ShareAlike 2.0 Belgium    *
 * disponible en ligne http://creativecommons.org/licenses/by-sa/2.0/be/ ou par courrier postal *
 * à Creative Commons, 171 Second Street, Suite 300, San Francisco, California 94105, USA.      *
 **/

public class CAPEmu extends Applet
{
private final static byte[] responseToSelect =	{
// Length 0x30 or 48
(byte)0x6F, (byte)0x2E, (byte)0x84, (byte)0x07, (byte)0xA0,
(byte)0x00, (byte)0x00, (byte)0x00, (byte)0x04, (byte)0x80,
(byte)0x02, (byte)0xA5, (byte)0x23, (byte)0x9F, (byte)0x38,
(byte)0x03, (byte)0x9F, (byte)0x35, (byte)0x01, (byte)0x5F,
(byte)0x2D, (byte)0x02, (byte)0x66, (byte)0x72, (byte)0xBF,
(byte)0x0c, (byte)0x15, (byte)0x9F, (byte)0x55, (byte)0x01,
(byte)0x00, (byte)0x5F, (byte)0x2C, (byte)0x02, (byte)0x00, 
(byte)0x56, (byte)0xDF, (byte)0x07, (byte)0x09, (byte)0x42, 
(byte)0x4B, (byte)0x53, (byte)0x30, (byte)0x35, (byte)0x36, 
(byte)0x36, (byte)0x35, (byte)0x31
};
	
private final static byte[] responseType =	{
// Length 0x10 or 16
(byte)0x77, (byte)0x0E, (byte)0x82, (byte)0x02, (byte)0x10, 
(byte)0x00, (byte)0x94, (byte)0x08, (byte)0x08, (byte)0x01, 
(byte)0x01, (byte)0x00, (byte)0x08, (byte)0x04, (byte)0x04, 
(byte)0x00
};

private final static byte[] Record1 =	{
// Length Ox40 or 64
(byte)0x70, (byte)0x3E, (byte)0x5A, (byte)0x09, (byte)0x67,
(byte)0x03, (byte)0x12, (byte)0x34, (byte)0x56, (byte)0x78,
(byte)0x90, (byte)0x12, (byte)0x3F, (byte)0x5F, (byte)0x34,
(byte)0x01, (byte)0x01, (byte)0x5F, (byte)0x25, (byte)0x03,
(byte)0x09, (byte)0x02, (byte)0x01, (byte)0x5F, (byte)0x24,
(byte)0x03, (byte)0x13, (byte)0x05, (byte)0x31, (byte)0x57,
(byte)0x13, (byte)0x67, (byte)0x03, (byte)0x12, (byte)0x34,
(byte)0x56, (byte)0x78, (byte)0x90, (byte)0x12, (byte)0x3D,
(byte)0x13, (byte)0x05, (byte)0x22, (byte)0x10, (byte)0x00,
(byte)0x00, (byte)0x02, (byte)0x00, (byte)0x00, (byte)0x9F,
(byte)0x5F, (byte)0x28, (byte)0x02, (byte)0x00, (byte)0x56,
(byte)0x9F, (byte)0x42, (byte)0x02, (byte)0x09, (byte)0x78,
(byte)0x9F, (byte)0x44, (byte)0x01, (byte)0x02
};

private final static byte[] Record2 =	{
// Length 0x5A or 90
(byte)0x70, (byte)0x58, (byte)0x9F, (byte)0x56, (byte)0x0B,
(byte)0x00, (byte)0x00, (byte)0xFF, (byte)0x00, (byte)0x00,
(byte)0x00, (byte)0x00, (byte)0x00, (byte)0x03, (byte)0xFF,
(byte)0xFF, (byte)0x8E, (byte)0x0A, (byte)0x00, (byte)0x00,
(byte)0x00, (byte)0x00, (byte)0x00, (byte)0x00, (byte)0x00,
(byte)0x00, (byte)0x01, (byte)0x00, (byte)0x8C, (byte)0x1B,
(byte)0x9F, (byte)0x02, (byte)0x06, (byte)0x9F, (byte)0x03,
(byte)0x06, (byte)0x9F, (byte)0x1A, (byte)0x02, (byte)0x95,
(byte)0x05, (byte)0x5F, (byte)0x2A, (byte)0x02, (byte)0x9A,
(byte)0x03, (byte)0x9C, (byte)0x01, (byte)0x9F, (byte)0x37,
(byte)0x04, (byte)0x9F, (byte)0x4C, (byte)0x02, (byte)0x9F,
(byte)0x34, (byte)0x03, (byte)0x8D, (byte)0x1F, (byte)0x8A,
(byte)0x02, (byte)0x9F, (byte)0x02, (byte)0x06, (byte)0x9F,
(byte)0x03, (byte)0x06, (byte)0x9F, (byte)0x1A, (byte)0x02,
(byte)0x95, (byte)0x05, (byte)0x5F, (byte)0x2A, (byte)0x02,
(byte)0x9A, (byte)0x03, (byte)0x9C, (byte)0x01, (byte)0x9F,
(byte)0x37, (byte)0x04, (byte)0x9F, (byte)0x4C, (byte)0x02,
(byte)0x9F, (byte)0x34, (byte)0x03, (byte)0x91, (byte)0x0A
};

private final static byte[] Crypto1 =	{
// Length 0x28 or 40
(byte)0x77, (byte)0x26, (byte)0x9F, (byte)0x27, (byte)0x01,
(byte)0x80, (byte)0x9F, (byte)0x36, (byte)0x02, (byte)0x00,
(byte)0x00, (byte)0x9F, (byte)0x26, (byte)0x08, (byte)0x00,
(byte)0x00, (byte)0x00, (byte)0x00, (byte)0x00, (byte)0x00,
(byte)0x00, (byte)0x00, (byte)0x9F, (byte)0x10, (byte)0x0F,
(byte)0x06, (byte)0x01, (byte)0x56, (byte)0x03, (byte)0xA4,
(byte)0x00, (byte)0x00, (byte)0x07, (byte)0x00, (byte)0x03,
(byte)0x00, (byte)0x00, (byte)0x01, (byte)0x00, (byte)0x02
};

private final static byte[] Crypto2 =	{
// Length 0x28 or 40
(byte)0x77, (byte)0x26, (byte)0x9F, (byte)0x27, (byte)0x01,
(byte)0x00, (byte)0x9F, (byte)0x36, (byte)0x02, (byte)0x00,
(byte)0x00, (byte)0x9F, (byte)0x26, (byte)0x08, (byte)0x00,
(byte)0x00, (byte)0x00, (byte)0x00, (byte)0x00, (byte)0x00,
(byte)0x00, (byte)0x00, (byte)0x9F, (byte)0x10, (byte)0x0F,
(byte)0x06, (byte)0x01, (byte)0x56, (byte)0x03, (byte)0x25,
(byte)0xB0, (byte)0x40, (byte)0x07, (byte)0x01, (byte)0x03,
(byte)0x00, (byte)0x00, (byte)0x01, (byte)0x00, (byte)0x02
};

private final static byte[] RetryLeft = {
(byte)0x9F, (byte)0x17, (byte)0x01, (byte)0x03
};

private byte[] pin = JCSystem.makeTransientByteArray((short)2, JCSystem.CLEAR_ON_DESELECT); 

  /** Basic Java Card applet registration */
  public static void install(byte[] bArray, short bOffset, byte bLength) {
	new CAPEmu().register();
	}

  public void process(APDU apdu) {
	short bytesP1;
	short readCount;
	short bytesLeft;
	byte[] buf = apdu.getBuffer();
	if (selectingApplet()) {
		Util.arrayCopyNonAtomic(responseToSelect,(byte)0,buf,ISO7816.OFFSET_CDATA,(short)responseToSelect.length);
		apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA,(short)responseToSelect.length);
		return;
		}

  switch (buf[ISO7816.OFFSET_INS]) {
	case (byte) 0xA8:
		readCount = apdu.setIncomingAndReceive();
		Util.arrayCopyNonAtomic(responseType,(byte)0,buf,ISO7816.OFFSET_CDATA,(short)responseType.length);
		apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA,(short)responseType.length);
		break;
	case (byte) 0xB2:
		switch (buf[ISO7816.OFFSET_P1])	{
		case (byte) 0x01:
			bytesLeft = apdu.setOutgoing();
			if (bytesLeft == (short) 0)	{
				apdu.setOutgoingLength((short) 0);
				apdu.sendBytesLong (Record1,(short)0,(short)0);
				}
			else	{
				apdu.setOutgoingLength((short)Record1.length);
				apdu.sendBytesLong (Record1,(short)0,(short)Record1.length);
				}
			break;
		case (short) 0x04:
			bytesLeft = apdu.setOutgoing();
			if (bytesLeft == (short) 0)	{
				apdu.setOutgoingLength((short) 0);
				apdu.sendBytesLong (Record2,(short)0,(short)0);
				}
			else	{
				apdu.setOutgoingLength((short)Record2.length);
				apdu.sendBytesLong (Record2,(short)0,(short)Record2.length);
				}
			break;
		default:
			ISOException.throwIt(ISO7816.SW_INCORRECT_P1P2);
			}		
		break;
	case (byte) 0xCA:
		bytesLeft = apdu.setOutgoing();
		if (bytesLeft == (short) 0)	{
			apdu.setOutgoingLength((short) 0);
			apdu.sendBytesLong (RetryLeft,(short)0,(short)0);
			}
		else	{
			apdu.setOutgoingLength((short)RetryLeft.length);
			apdu.sendBytesLong (RetryLeft,(short)0,(short)RetryLeft.length);
			}
		break;
	case (byte) 0x20:
		readCount = apdu.setIncomingAndReceive();
		Util.arrayCopyNonAtomic(buf,(byte)(ISO7816.OFFSET_CDATA + 1),pin,(byte)0,(short)pin.length);
		break;
	case (byte) 0xAE:
		switch (buf[ISO7816.OFFSET_P1])	{
		case (byte) 0x80:
			readCount = apdu.setIncomingAndReceive();
			Util.arrayCopyNonAtomic(Crypto1,(byte)0,buf,ISO7816.OFFSET_CDATA,(short)Crypto1.length);
			// put the PIN value back in the last 2 bytes of the cryptogram
			Util.arrayCopyNonAtomic(pin,(byte)0,buf,(byte)(ISO7816.OFFSET_CDATA + 20),(short)pin.length);
			apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA,(short)Crypto1.length);
			break;
		case (byte) 0x00:
			readCount = apdu.setIncomingAndReceive();
			Util.arrayCopyNonAtomic(Crypto2,(byte)0,buf,ISO7816.OFFSET_CDATA,(short)Crypto2.length);
			apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA,(short)Crypto2.length);
			break;
		default:
			ISOException.throwIt(ISO7816.SW_INCORRECT_P1P2);
			}
		break;

	default:
		// good practice: If you don't know the INStruction, say so:
		ISOException.throwIt(ISO7816.SW_INS_NOT_SUPPORTED);
		}
	}
}
