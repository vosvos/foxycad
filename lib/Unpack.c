/*
 * The Python Imaging Library.
 * $Id: //modules/pil/libImaging/Unpack.c#3 $
 *
 * code to unpack raw data from various file formats
 *
 * history:
 * 96-03-07 fl	Created (from various decoders)
 * 96-04-19 fl	Added band unpackers
 * 96-05-12 fl	Published RGB unpackers
 * 96-05-27 fl	Added nibble unpacker
 * 96-12-10 fl	Added complete set of PNG unpackers
 * 96-12-29 fl	Set alpha byte in RGB unpackers
 * 97-01-05 fl	Added remaining TGA unpackers
 * 97-01-18 fl	Added inverting band unpackers
 * 97-01-25 fl	Added FlashPix unpackers
 * 97-05-31 fl	Added floating point unpackers
 * 98-02-08 fl	Added I unpacker
 * 98-07-01 fl	Added YCbCr unpacker
 * 98-07-02 fl	Added full set of integer unpackers
 * 98-12-29 fl	Added mode field, I;16 unpackers
 * 98-12-30 fl	Added RGBX modes
 * 99-02-04 fl	Fixed I;16 unpackers
 *
 * Copyright (c) Secret Labs AB 1997-99.
 * Copyright (c) Fredrik Lundh 1996-97.
 *
 * See the README file for information on usage and redistribution.
 */


#include "Imaging.h"


#define	R 0
#define	G 1
#define	B 2
#define	X 3

#define	A 3

#define	C 0
#define	M 1
#define	Y 2
#define	K 3


/* byte-swapping macros */

#define C16N\
        (tmp[0]=in[0], tmp[1]=in[1]);
#define C16S\
        (tmp[1]=in[0], tmp[0]=in[1]);
#define C32N\
        (tmp[0]=in[0], tmp[1]=in[1], tmp[2]=in[2], tmp[3]=in[3]);
#define C32S\
        (tmp[3]=in[0], tmp[2]=in[1], tmp[1]=in[2], tmp[0]=in[3]);
#define C64N\
        (tmp[0]=in[0], tmp[1]=in[1], tmp[2]=in[2], tmp[3]=in[3],\
         tmp[4]=in[4], tmp[5]=in[5], tmp[6]=in[6], tmp[7]=in[7]);
#define C64S\
        (tmp[7]=in[0], tmp[6]=in[1], tmp[5]=in[2], tmp[4]=in[3],\
         tmp[3]=in[4], tmp[2]=in[5], tmp[1]=in[6], tmp[0]=in[7]);

#ifdef WORDS_BIGENDIAN
#define C16B C16N
#define C16L C16S
#define C32B C32N
#define C32L C32S
#define C64B C64N
#define C64L C64S
#else
#define C16B C16S
#define C16L C16N
#define C32B C32S
#define C32L C32N
#define C64B C64S
#define C64L C64N
#endif

/* Unpack to "1" image */

static void
unpack1(UINT8* out, const UINT8* in, int pixels)
{
    /* bits (msb first, white is non-zero) */
    while (pixels > 0) {
	UINT8 byte = *in++;
	switch (pixels) {
	default:    *out++ = (byte & 128) ? 255 : 0; byte <<= 1;
	case 7:	    *out++ = (byte & 128) ? 255 : 0; byte <<= 1;
	case 6:	    *out++ = (byte & 128) ? 255 : 0; byte <<= 1;
	case 5:	    *out++ = (byte & 128) ? 255 : 0; byte <<= 1;
	case 4:	    *out++ = (byte & 128) ? 255 : 0; byte <<= 1;
	case 3:	    *out++ = (byte & 128) ? 255 : 0; byte <<= 1;
	case 2:	    *out++ = (byte & 128) ? 255 : 0; byte <<= 1;
	case 1:	    *out++ = (byte & 128) ? 255 : 0;
	}
	pixels -= 8;
    }
}

static void
unpack1I(UINT8* out, const UINT8* in, int pixels)
{
    /* bits (msb first, white is zero) */
    while (pixels > 0) {
	UINT8 byte = *in++;
	switch (pixels) {
	default:    *out++ = (byte & 128) ? 0 : 255; byte <<= 1;
	case 7:	    *out++ = (byte & 128) ? 0 : 255; byte <<= 1;
	case 6:	    *out++ = (byte & 128) ? 0 : 255; byte <<= 1;
	case 5:	    *out++ = (byte & 128) ? 0 : 255; byte <<= 1;
	case 4:	    *out++ = (byte & 128) ? 0 : 255; byte <<= 1;
	case 3:	    *out++ = (byte & 128) ? 0 : 255; byte <<= 1;
	case 2:	    *out++ = (byte & 128) ? 0 : 255; byte <<= 1;
	case 1:	    *out++ = (byte & 128) ? 0 : 255;
	}
	pixels -= 8;
    }
}

static void
unpack1R(UINT8* out, const UINT8* in, int pixels)
{
    /* bits (lsb first, white is non-zero) */
    while (pixels > 0) {
	UINT8 byte = *in++;
	switch (pixels) {
	default:    *out++ = (byte & 1) ? 255 : 0; byte >>= 1;
	case 7:	    *out++ = (byte & 1) ? 255 : 0; byte >>= 1;
	case 6:	    *out++ = (byte & 1) ? 255 : 0; byte >>= 1;
	case 5:	    *out++ = (byte & 1) ? 255 : 0; byte >>= 1;
	case 4:	    *out++ = (byte & 1) ? 255 : 0; byte >>= 1;
	case 3:	    *out++ = (byte & 1) ? 255 : 0; byte >>= 1;
	case 2:	    *out++ = (byte & 1) ? 255 : 0; byte >>= 1;
	case 1:	    *out++ = (byte & 1) ? 255 : 0;
	}
	pixels -= 8;
    }
}

static void
unpack1IR(UINT8* out, const UINT8* in, int pixels)
{
    /* bits (lsb first, white is zero) */
    while (pixels > 0) {
	UINT8 byte = *in++;
	switch (pixels) {
	default:    *out++ = (byte & 1) ? 0 : 255; byte >>= 1;
	case 7:	    *out++ = (byte & 1) ? 0 : 255; byte >>= 1;
	case 6:	    *out++ = (byte & 1) ? 0 : 255; byte >>= 1;
	case 5:	    *out++ = (byte & 1) ? 0 : 255; byte >>= 1;
	case 4:	    *out++ = (byte & 1) ? 0 : 255; byte >>= 1;
	case 3:	    *out++ = (byte & 1) ? 0 : 255; byte >>= 1;
	case 2:	    *out++ = (byte & 1) ? 0 : 255; byte >>= 1;
	case 1:	    *out++ = (byte & 1) ? 0 : 255;
	}
	pixels -= 8;
    }
}


/* Unpack to "L" image */

static void
unpackL2(UINT8* out, const UINT8* in, int pixels)
{
    /* nibbles */
    while (pixels > 0) {
	UINT8 byte = *in++;
	switch (pixels) {
	default:    *out++ = ((byte >> 6) & 3) * 255 / 3; byte <<= 2;
	case 3:	    *out++ = ((byte >> 6) & 3) * 255 / 3; byte <<= 2;
	case 2:	    *out++ = ((byte >> 6) & 3) * 255 / 3; byte <<= 2;
	case 1:	    *out++ = ((byte >> 6) & 3) * 255 / 3;
	}
	pixels -= 4;
    }
}

static void
unpackL4(UINT8* out, const UINT8* in, int pixels)
{
    /* nibbles */
    while (pixels > 0) {
	UINT8 byte = *in++;
	switch (pixels) {
	default:    *out++ = ((byte >> 4) & 15) * 255 / 15; byte <<= 4;
	case 1:	    *out++ = ((byte >> 4) & 15) * 255 / 15;
	}
	pixels -= 2;
    }
}

static void
unpackLI(UINT8* out, const UINT8* in, int pixels)
{
    /* negative */
    int i;
    for (i = 0; i < pixels; i++)
	out[i] = ~in[i];
}

static void
unpackL16(UINT8* out, const UINT8* in, int pixels)
{
    /* int16 (upper byte, little endian) */
    int i;
    for (i = 0; i < pixels; i++) {
	out[i] = in[1];
	in += 2;
    }
}

static void
unpackL16B(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* int16 (upper byte, big endian) */
    for (i = 0; i < pixels; i++) {
	out[i] = in[0];
	in += 2;
    }
}


/* Unpack to "P" image */

static void
unpackP1(UINT8* out, const UINT8* in, int pixels)
{
    /* bits */
    while (pixels > 0) {
	UINT8 byte = *in++;
	switch (pixels) {
	default:    *out++ = (byte >> 7) & 1; byte <<= 1;
	case 7:	    *out++ = (byte >> 7) & 1; byte <<= 1;
	case 6:	    *out++ = (byte >> 7) & 1; byte <<= 1;
	case 5:	    *out++ = (byte >> 7) & 1; byte <<= 1;
	case 4:	    *out++ = (byte >> 7) & 1; byte <<= 1;
	case 3:	    *out++ = (byte >> 7) & 1; byte <<= 1;
	case 2:	    *out++ = (byte >> 7) & 1; byte <<= 1;
	case 1:	    *out++ = (byte >> 7) & 1;
	}
	pixels -= 8;
    }
}

static void
unpackP2(UINT8* out, const UINT8* in, int pixels)
{
    /* bit pairs */
    while (pixels > 0) {
	UINT8 byte = *in++;
	switch (pixels) {
	default:    *out++ = (byte >> 6) & 3; byte <<= 2;
	case 3:	    *out++ = (byte >> 6) & 3; byte <<= 2;
	case 2:	    *out++ = (byte >> 6) & 3; byte <<= 2;
	case 1:	    *out++ = (byte >> 6) & 3;
	}
	pixels -= 4;
    }
}

static void
unpackP4(UINT8* out, const UINT8* in, int pixels)
{
    /* nibbles */
    while (pixels > 0) {
	UINT8 byte = *in++;
	switch (pixels) {
	default:    *out++ = (byte >> 4) & 15; byte <<= 4;
	case 1:	    *out++ = (byte >> 4) & 15;
	}
	pixels -= 2;
    }
}

static void
unpackP2L(UINT8* out, const UINT8* in, int pixels)
{
    int i, j, m, s;
    /* bit layers */
    m = 128;
    s = (pixels+7)/8;
    for (i = j = 0; i < pixels; i++) {
	out[i] = ((in[j] & m) ? 1 : 0) + ((in[j + s] & m) ? 2 : 0);
	if ((m >>= 1) == 0) {
	    m = 128;
	    j++;
	}
    }
}

static void
unpackP4L(UINT8* out, const UINT8* in, int pixels)
{
    int i, j, m, s;
    /* bit layers (trust the optimizer ;-) */
    m = 128;
    s = (pixels+7)/8;
    for (i = j = 0; i < pixels; i++) {
	out[i] = ((in[j] & m) ? 1 : 0) + ((in[j + s] & m) ? 2 : 0) +
		 ((in[j + 2*s] & m) ? 4 : 0) + ((in[j + 3*s] & m) ? 8 : 0);
	if ((m >>= 1) == 0) {
	    m = 128;
	    j++;
	}
    }
}

/* Unpack to "RGB" image */

void
ImagingUnpackRGB(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* RGB triplets */
    for (i = 0; i < pixels; i++) {
	out[R] = in[0];
	out[G] = in[1];
	out[B] = in[2];
	out[A] = 255;
	out += 4; in += 3;
    }
}

void
unpackRGB16B(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* 16-bit RGB triplets, big-endian order */
    for (i = 0; i < pixels; i++) {
	out[R] = in[0];
	out[G] = in[2];
	out[B] = in[4];
	out[A] = 255;
	out += 4; in += 6;
    }
}

static void
unpackRGBL(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* RGB, line interleaved */
    for (i = 0; i < pixels; i++) {
	out[R] = in[i];
	out[G] = in[i+pixels];
	out[B] = in[i+pixels+pixels];
	out[A] = 255;
	out += 4;
    }
}


void
ImagingUnpackBGR(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* RGB, reversed bytes */
    for (i = 0; i < pixels; i++) {
	out[R] = in[2];
	out[G] = in[1];
	out[B] = in[0];
	out[A] = 255;
	out += 4; in += 3;
    }
}

void
ImagingUnpackBGR15(UINT8* out, const UINT8* in, int pixels)
{
    int i, pixel;
    /* RGB, reversed bytes, 5 bits per pixel */
    for (i = 0; i < pixels; i++) {
	pixel = in[0] + (in[1] << 8);
	out[B] = (pixel & 31) * 255 / 31;
	out[G] = ((pixel>>5) & 31) * 255 / 31;
	out[R] = ((pixel>>10) & 31) * 255 / 31;
	out[A] = 255;
	out += 4; in += 2;
    }
}

void
ImagingUnpackBGR16(UINT8* out, const UINT8* in, int pixels)
{
    int i, pixel;
    /* RGB, reversed bytes, 5/6/5 bits per pixel */
    for (i = 0; i < pixels; i++) {
	pixel = in[0] + (in[1] << 8);
	out[B] = (pixel & 31) * 255 / 31;
	out[G] = ((pixel>>5) & 63) * 255 / 63;
	out[R] = ((pixel>>11) & 31) * 255 / 31;
	out[A] = 255;
	out += 4; in += 2;
    }
}

static void
ImagingUnpackBGRX(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* RGB, reversed bytes with padding */
    for (i = 0; i < pixels; i++) {
	out[R] = in[2];
	out[G] = in[1];
	out[B] = in[0];
	out[A] = 255;
	out += 4; in += 4;
    }
}

static void
ImagingUnpackXRGB(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* RGB, leading pad */
    for (i = 0; i < pixels; i++) {
	out[R] = in[1];
	out[G] = in[2];
	out[B] = in[3];
	out[A] = 255;
	out += 4; in += 4;
    }
}

static void
ImagingUnpackXBGR(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* RGB, reversed bytes, leading pad */
    for (i = 0; i < pixels; i++) {
	out[R] = in[3];
	out[G] = in[2];
	out[B] = in[1];
	out[A] = 255;
	out += 4; in += 4;
    }
}

/* Unpack to "RGBA" image */

static void
unpackLA(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* greyscale with alpha */
    for (i = 0; i < pixels; i++) {
	out[R] = out[G] = out[B] = in[0];
	out[A] = in[1];
	out += 4; in += 2;
    }
}

static void
unpackLA16B(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* 16-bit greyscale with alpha, big-endian */
    for (i = 0; i < pixels; i++) {
	out[R] = out[G] = out[B] = in[0];
	out[A] = in[2];
	out += 4; in += 4;
    }
}

static void
unpackRGBAI(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* RGBA, inverted RGB bytes (FlashPix) */
    for (i = 0; i < pixels; i++) {
	out[R] = ~in[0];
	out[G] = ~in[1];
	out[B] = ~in[2];
	out[A] = in[3];
	out += 4; in += 4;
    }
}

static void
unpackRGBAL(UINT8* out, const UINT8* in, int pixels)
{
    int i;

    /* RGBA, line interleaved */
    for (i = 0; i < pixels; i++) {
	out[R] = in[i];
	out[G] = in[i+pixels];
	out[B] = in[i+pixels+pixels];
	out[A] = in[i+pixels+pixels+pixels];
	out += 4;
    }
}

void
unpackRGBA16B(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* 16-bit RGBA, big-endian order */
    for (i = 0; i < pixels; i++) {
	out[R] = in[0];
	out[G] = in[2];
	out[B] = in[4];
	out[A] = in[6];
	out += 4; in += 8;
    }
}

static void
unpackARGB(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* RGBA, leading pad */
    for (i = 0; i < pixels; i++) {
	out[R] = in[1];
	out[G] = in[2];
	out[B] = in[3];
	out[A] = in[0];
	out += 4; in += 4;
    }
}

static void
unpackABGR(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* RGBA, reversed bytes */
    for (i = 0; i < pixels; i++) {
	out[R] = in[3];
	out[G] = in[2];
	out[B] = in[1];
	out[A] = in[0];
	out += 4; in += 4;
    }
}

static void
unpackBGRA(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* RGBA, reversed bytes */
    for (i = 0; i < pixels; i++) {
	out[R] = in[2];
	out[G] = in[1];
	out[B] = in[0];
	out[A] = in[3];
	out += 4; in += 4;
    }
}


/* Unpack to "CMYK" image */

static void
unpackCMYKI(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* CMYK, inverted bytes (Photoshop 2.5) */
    for (i = 0; i < pixels; i++) {
	out[C] = ~in[0];
	out[M] = ~in[1];
	out[Y] = ~in[2];
	out[K] = ~in[3];
	out += 4; in += 4;
    }
}

static void
copy1(UINT8* out, const UINT8* in, int pixels)
{
    /* L, P */
    memcpy(out, in, pixels);
}

static void
copy2(UINT8* out, const UINT8* in, int pixels)
{
    /* I;16 */
    memcpy(out, in, pixels*2);
}

static void
copy4(UINT8* out, const UINT8* in, int pixels)
{
    /* RGBA, CMYK quadruples */
    memcpy(out, in, 4 * pixels);
}


/* Unpack to "I" and "F" images */

#define UNPACK_RAW(NAME, GET, INTYPE, OUTTYPE)\
static void NAME(UINT8* out_, const UINT8* in, int pixels)\
{\
    int i;\
    OUTTYPE* out = (OUTTYPE*) out_;\
    for (i = 0; i < pixels; i++, in += sizeof(INTYPE))\
        out[i] = (OUTTYPE) ((INTYPE) GET);\
}

#define UNPACK(NAME, COPY, INTYPE, OUTTYPE)\
static void NAME(UINT8* out_, const UINT8* in, int pixels)\
{\
    int i;\
    OUTTYPE* out = (OUTTYPE*) out_;\
    INTYPE tmp_;\
    UINT8* tmp = (UINT8*) &tmp_;\
    for (i = 0; i < pixels; i++, in += sizeof(INTYPE)) {\
        COPY;\
        out[i] = (OUTTYPE) tmp_;\
    }\
}

UNPACK_RAW(unpackI8, in[0], UINT8, INT32)
UNPACK_RAW(unpackI8S, in[0], INT8, INT32)
UNPACK(unpackI16, C16L, UINT16, INT32)
UNPACK(unpackI16S, C16L, INT16, INT32)
UNPACK(unpackI16B, C16B, UINT16, INT32)
UNPACK(unpackI16BS, C16B, INT16, INT32)
UNPACK(unpackI16N, C16N, UINT16, INT32)
UNPACK(unpackI16NS, C16N, INT16, INT32)
UNPACK(unpackI32, C32L, UINT32, INT32)
UNPACK(unpackI32S, C32L, INT32, INT32)
UNPACK(unpackI32B, C32B, UINT32, INT32)
UNPACK(unpackI32BS, C32B, INT32, INT32)
UNPACK(unpackI32N, C32N, UINT32, INT32)
UNPACK(unpackI32NS, C32N, INT32, INT32)

UNPACK_RAW(unpackF8, in[0], UINT8, FLOAT32)
UNPACK_RAW(unpackF8S, in[0], INT8, FLOAT32)
UNPACK(unpackF16, C16L, UINT16, FLOAT32)
UNPACK(unpackF16S, C16L, INT16, FLOAT32)
UNPACK(unpackF16B, C16B, UINT16, FLOAT32)
UNPACK(unpackF16BS, C16B, INT16, FLOAT32)
UNPACK(unpackF16N, C16N, UINT16, FLOAT32)
UNPACK(unpackF16NS, C16N, INT16, FLOAT32)
UNPACK(unpackF32, C32L, UINT32, FLOAT32)
UNPACK(unpackF32S, C32L, INT32, FLOAT32)
UNPACK(unpackF32B, C32B, UINT32, FLOAT32)
UNPACK(unpackF32BS, C32B, INT32, FLOAT32)
UNPACK(unpackF32N, C32N, UINT32, FLOAT32)
UNPACK(unpackF32NS, C32N, INT32, FLOAT32)
UNPACK(unpackF32F, C32L, FLOAT32, FLOAT32)
UNPACK(unpackF32BF, C32B, FLOAT32, FLOAT32)
UNPACK(unpackF32NF, C32N, FLOAT32, FLOAT32)
#ifdef FLOAT64
UNPACK(unpackF64F, C64L, FLOAT64, FLOAT32)
UNPACK(unpackF64BF, C64B, FLOAT64, FLOAT32)
UNPACK(unpackF64NF, C64N, FLOAT64, FLOAT32)
#endif


/* Misc. unpackers */

static void
band0(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* band 0 only */
    for (i = 0; i < pixels; i++) {
	out[0] = in[i];
	out += 4;
    }
}

static void
band1(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* band 1 only */
    for (i = 0; i < pixels; i++) {
	out[1] = in[i];
	out += 4;
    }
}

static void
band2(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* band 2 only */
    for (i = 0; i < pixels; i++) {
	out[2] = in[i];
	out += 4;
    }
}

static void
band3(UINT8* out, const UINT8* in, int pixels)
{
    /* band 3 only */
    int i;
    for (i = 0; i < pixels; i++) {
	out[3] = in[i];
	out += 4;
    }
}

static void
band0I(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* band 0 only */
    for (i = 0; i < pixels; i++) {
	out[0] = ~in[i];
	out += 4;
    }
}

static void
band1I(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* band 1 only */
    for (i = 0; i < pixels; i++) {
	out[1] = ~in[i];
	out += 4;
    }
}

static void
band2I(UINT8* out, const UINT8* in, int pixels)
{
    int i;
    /* band 2 only */
    for (i = 0; i < pixels; i++) {
	out[2] = ~in[i];
	out += 4;
    }
}

static void
band3I(UINT8* out, const UINT8* in, int pixels)
{
    /* band 3 only */
    int i;
    for (i = 0; i < pixels; i++) {
	out[3] = ~in[i];
	out += 4;
    }
}

static struct {
    const char* mode;
    const char* rawmode;
    int bits;
    ImagingShuffler unpack;
} unpackers[] = {

    /* bilevel */
    {"1",	"1",		1,	unpack1},
    {"1",	"1;I",		1,	unpack1I},
    {"1",	"1;R",		1,	unpack1R},
    {"1",	"1;IR",		1,	unpack1IR},

    /* greyscale */
    {"L",	"L;2",  	2,	unpackL2},
    {"L",	"L;4",  	4,	unpackL4},
    {"L",	"L",   		8,	copy1},
    {"L",	"L;I",   	8,	unpackLI},
    {"L",	"L;16",  	16,	unpackL16},
    {"L",	"L;16B",  	16,	unpackL16B},

    /* palette */
    {"P",	"P;1",   	1,	unpackP1},
    {"P",	"P;2",   	2,	unpackP2},
    {"P",	"P;2L",   	2,	unpackP2L},
    {"P",	"P;4",   	4,	unpackP4},
    {"P",	"P;4L",   	4,	unpackP4L},
    {"P",	"P",		8,	copy1},

    /* true colour */
    {"RGB",	"RGB",		24,	ImagingUnpackRGB},
    {"RGB",	"RGB;L",	24,	unpackRGBL},
    {"RGB",	"RGB;16B",	48,	unpackRGB16B},
    {"RGB",	"BGR",		24,	ImagingUnpackBGR},
    {"RGB",	"BGR;15",	16,	ImagingUnpackBGR15},
    {"RGB",	"BGR;16",	16,	ImagingUnpackBGR16},
    {"RGB",	"BGR;5",	16,	ImagingUnpackBGR15}, /* compat */
    {"RGB",	"RGBX",		32,	copy4},
    {"RGB",	"RGBX;L",	32,	unpackRGBAL},
    {"RGB",	"BGRX",		32,	ImagingUnpackBGRX},
    {"RGB",	"XRGB",		24,	ImagingUnpackXRGB},
    {"RGB",	"XBGR",		32,	ImagingUnpackXBGR},
    {"RGB",	"YCC;P",	24,	ImagingUnpackYCC},
    {"RGB",	"R",   		8,	band0},
    {"RGB",	"G",   		8,	band1},
    {"RGB",	"B",   		8,	band2},

    /* true colour w. transparency */
    {"RGBA",	"LA",		16,	unpackLA},
    {"RGBA",	"LA;16B",	32,	unpackLA16B},
    {"RGBA",	"RGBA",		32,	copy4},
    {"RGBA",	"RGBA;I",	32,	unpackRGBAI},
    {"RGBA",	"RGBA;L",	32,	unpackRGBAL},
    {"RGBA",	"RGBA;16B",	64,	unpackRGBA16B},
    {"RGBA",	"BGRA",		32,	unpackBGRA},
    {"RGBA",	"ARGB",		32,	unpackARGB},
    {"RGBA",	"ABGR",		32,	unpackABGR},
    {"RGBA",	"YCCA;P",	32,	ImagingUnpackYCCA},
    {"RGBA",	"R",   		8,	band0},
    {"RGBA",	"G",   		8,	band1},
    {"RGBA",	"B",   		8,	band2},
    {"RGBA",	"A",   		8,	band3},

    /* true colour w. padding */
    {"RGBX",	"RGB",		24,	ImagingUnpackRGB},
    {"RGBX",	"RGB;L",	24,	unpackRGBL},
    {"RGBX",	"RGB;16B",	48,	unpackRGB16B},
    {"RGBX",	"BGR",		24,	ImagingUnpackBGR},
    {"RGBX",	"BGR;15",	16,	ImagingUnpackBGR15},
    {"RGB",	"BGR;16",	16,	ImagingUnpackBGR16},
    {"RGBX",	"BGR;5",	16,	ImagingUnpackBGR15}, /* compat */
    {"RGBX",	"RGBX",		32,	copy4},
    {"RGBX",	"RGBX;L",	32,	unpackRGBAL},
    {"RGBX",	"BGRX",		32,	ImagingUnpackBGRX},
    {"RGBX",	"XRGB",		24,	ImagingUnpackXRGB},
    {"RGBX",	"XBGR",		32,	ImagingUnpackXBGR},
    {"RGBX",	"YCC;P",	24,	ImagingUnpackYCC},
    {"RGBX",	"R",   		8,	band0},
    {"RGBX",	"G",   		8,	band1},
    {"RGBX",	"B",   		8,	band2},
    {"RGBX",	"X",   		8,	band3},

    /* colour separation */
    {"CMYK",	"CMYK",		32,	copy4},
    {"CMYK",	"CMYK;I",	32,	unpackCMYKI},
    {"CMYK",	"CMYK;L",	32,	unpackRGBAL},
    {"CMYK",	"C",   		8,	band0},
    {"CMYK",	"M",   		8,	band1},
    {"CMYK",	"Y",   		8,	band2},
    {"CMYK",	"K",   		8,	band3},
    {"CMYK",	"C;I",   	8,	band0I},
    {"CMYK",	"M;I",   	8,	band1I},
    {"CMYK",	"Y;I",   	8,	band2I},
    {"CMYK",	"K;I",   	8,	band3I},

    /* video (YCbCr) */
    {"YCbCr",	"YCbCr",	24,	ImagingUnpackRGB},
    {"YCbCr",	"YCbCr;L",	24,	unpackRGBL},
    {"YCbCr",	"YCbCrX",	32,	copy4},
    {"YCbCr",	"YCbCrK",	32,	copy4},

    /* integer variations */
    {"I",	"I",		32,	copy4},
    {"I",	"I;8",		8,	unpackI8},
    {"I",	"I;8S",		8,	unpackI8S},
    {"I",	"I;16",		16,	unpackI16},
    {"I",	"I;16S",	16,	unpackI16S},
    {"I",	"I;16B",	16,	unpackI16B},
    {"I",	"I;16BS",	16,	unpackI16BS},
    {"I",	"I;16N",	16,	unpackI16N},
    {"I",	"I;16NS",	16,	unpackI16NS},
    {"I",	"I;32",		32,	unpackI32},
    {"I",	"I;32S",	32,	unpackI32S},
    {"I",	"I;32B",	32,	unpackI32B},
    {"I",	"I;32BS",	32,	unpackI32BS},
    {"I",	"I;32N",	32,	unpackI32N},
    {"I",	"I;32NS",	32,	unpackI32NS},

    /* floating point variations */
    {"F",	"F",		32,	copy4},
    {"F",	"F;8",		8,	unpackF8},
    {"F",	"F;8S",		8,	unpackF8S},
    {"F",	"F;16",		16,	unpackF16},
    {"F",	"F;16S",	16,	unpackF16S},
    {"F",	"F;16B",	16,	unpackF16B},
    {"F",	"F;16BS",	16,	unpackF16BS},
    {"F",	"F;16N",	16,	unpackF16N},
    {"F",	"F;16NS",	16,	unpackF16NS},
    {"F",	"F;32",		32,	unpackF32},
    {"F",	"F;32S",	32,	unpackF32S},
    {"F",	"F;32B",	32,	unpackF32B},
    {"F",	"F;32BS",	32,	unpackF32BS},
    {"F",	"F;32N",	32,	unpackF32N},
    {"F",	"F;32NS",	32,	unpackF32NS},
    {"F",	"F;32F",	32,	unpackF32F},
    {"F",	"F;32BF",	32,	unpackF32BF},
    {"F",	"F;32NF",	32,	unpackF32NF},
#ifdef FLOAT64
    {"F",	"F;64F",	64,	unpackF64F},
    {"F",	"F;64BF",	64,	unpackF64BF},
    {"F",	"F;64NF",	64,	unpackF64NF},
#endif

    /* storage modes */
    {"I;16",	"I;16",		16,	copy2},
    {"I;16B",	"I;16B",	16,	copy2},

    {NULL} /* sentinel */
};


ImagingShuffler
ImagingFindUnpacker(const char* mode, const char* rawmode, int* bits_out)
{
    int i;

    /* find a suitable pixel unpacker */
    for (i = 0; unpackers[i].rawmode; i++)
	if (strcmp(unpackers[i].mode, mode) == 0 &&
            strcmp(unpackers[i].rawmode, rawmode) == 0) {
	    if (bits_out)
		*bits_out = unpackers[i].bits;
	    return unpackers[i].unpack;
	}
    return NULL;
}
