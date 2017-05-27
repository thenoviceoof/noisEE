#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/sleep.h>

// Forward declares.

uint16_t interpolatePiecewiseLinearFunction(uint16_t unpaddedX,
                                            uint16_t xs[8], uint16_t ys[8]);

void writeDisableWriteProtect();

void writeFilterValue(int value);

void writeSPIValue(char byte);

/**
 * Fix point constants for mapping the color value to the various
 * filter parameters.
 *
 * The numbers represent a piecewise linear approximation to the
 * parameter functions. The maximum "Y" value caps out at 2**15; the
 * hardware component values are chosen to get the right scale. There
 * are only 2**10 possible pot values, but snapping these
 * approximation values to the nearest 10 bit value would give up some
 * accuracy in the interpolation.
 *
 * The domain is scaled to fill 2**15: there are only 2**10 ADC
 * values, but we want more accuracy, similar to the range argument
 * given above.
 *
 * The interpolation calculation uses 32 bit ints, treating the 15 bit
 * filter parameter and 10 bit input as fixed point numbers.
 *
 * We use 2 bytes because 1 byte only covers 8 bits, and we have 10
 * bits of input and output. This way, we do not drop accuracy
 * needlessly.
 */
uint16_t filter0016x[8] = {0, 5734, 11693, 16030, 19274, 21684, 29121, 32767};
uint16_t filter0016y[8] = {0, 1478, 6579, 13111, 22962, 26764, 29850, 32767};

uint16_t filter0270x[8] = {0, 3400, 9726, 16331, 19395, 22078, 25416, 32767};
uint16_t filter0270y[8] = {1612, 6132, 22206, 32767, 13003, 4342, 807, 0};

uint16_t filter5300x[8] = {0, 2219, 7419, 10704, 16275, 20965, 24791, 32767};
uint16_t filter5300y[8] = {5264, 10757, 28662, 32767, 29869, 8733, 1838, 0};

// Plain white noise source filter parameters.
uint16_t filter0000x[8] = {0, 3468, 9517, 11880, 15385, 25149, 28630, 32767};
uint16_t filter0000y[8] = {32767, 32249, 10444, 5091, 1519, 363, 180, 80};

void calculateFilterParameters(uint16_t input, uint16_t *filter0016,
                               uint16_t *filter0270, uint16_t *filter5300,
                               uint16_t *filter0000) {
        // Cap the input at legal values for 10 bits of input, since
        // the ADC maxes out at 10 bits.
        if(input < 0) {
                input = 0;
        }
        if(input > 1023) {
                input = 1023;
        }

        // For each filter, interpolate the real value from the filter
        // definition arrays.
        *filter0016 = interpolatePiecewiseLinearFunction(
                input, filter0016x, filter0016y);
        *filter0270 = interpolatePiecewiseLinearFunction(
                input, filter0270x, filter0270y);
        *filter5300 = interpolatePiecewiseLinearFunction(
                input, filter5300x, filter5300y);
        *filter0000 = interpolatePiecewiseLinearFunction(
                input, filter0000x, filter0000y);

        // Cap the values at both ends.
        if(*filter0016 > 1023) {
                *filter0016 = 1023;
        }
        if(*filter0016 < 0) {
                *filter0016 = 0;
        }
        if(*filter0270 > 1023) {
                *filter0270 = 1023;
        }
        if(*filter0270 < 0) {
                *filter0270 = 0;
        }
        if(*filter5300 > 1023) {
                *filter5300 = 1023;
        }
        if(*filter5300 < 0) {
                *filter5300 = 0;
        }
        if(*filter0000 > 1023) {
                *filter0000 = 1023;
        }
        if(*filter0000 < 0) {
                *filter0000 = 0;
        }
}

uint16_t interpolatePiecewiseLinearFunction(uint16_t unpaddedX,
                                            uint16_t xs[8], uint16_t ys[8]) {
        // x is a 10-bit value, make it comparable to the 15-bit domain values.
        uint16_t x = (unpaddedX << 5);
        
        // Binary search through the xs array to find the two values
        // we should be interpolating between.
        // The current index represents the range that we expect the
        // value to be within.
        char minIndex = 0;
        char maxIndex = 6; // The max index is 7, but it's just an endpoint.
        while(minIndex != maxIndex) {
                char midIndex = (minIndex + maxIndex)/2;
                if(x < xs[midIndex]) {
                        maxIndex = midIndex - 1;
                } else if(x > xs[midIndex + 1]) {
                        minIndex = midIndex + 1;
                } else { // x >= xs[midIndex] && x <= xs[midIndex + 1]
                        maxIndex = midIndex;
                        break;
                }
        }

        // Now, maxIndex is the index of the lower endpoint of the
        // segment containing the value.
        // Since we're subtracting from the lower endpoint, our value
        // will always be positive.
        uint16_t t = x - xs[maxIndex];
        // Interpolate within the range of values.
        // Using a 16 bit signed value is fine, since we're dealing
        // with 15 bit values.
        int16_t dx = xs[maxIndex + 1] - xs[maxIndex];
        int16_t dy = ys[maxIndex + 1] - ys[maxIndex];
        // Theoretically possible for the intermediate value to take
        // up 15 + 15 = 30 bits, so use a signed 32 bit int.
        // The final delta should again fit into 15 bits.
        int16_t delta = ((int32_t) (dy * t)) / dx;
        // Reduce back to 10 bits.
        return (ys[maxIndex] + delta) >> 5;
}

/**
 * The previous output value of the individual filter parameters.
 */
int PREVIOUS_FILTER_0016 = 0;
int PREVIOUS_FILTER_0270 = 0;
int PREVIOUS_FILTER_5300 = 0;
int PREVIOUS_FILTER_0000 = 0;

void calculateAndWriteFilterValues(int input) {
        int filter0016 = 0;
        int filter0270 = 0;
        int filter5300 = 0;
        int filter0000 = 0;
        calculateFilterParameters(
                input,
                &filter0016,
                &filter0270,
                &filter5300,
                &filter0000
                );

        // For each device, select and then write the value over SPI.
        // Note that the active pin is LOW, not HIGH.
        if (filter0016 != PREVIOUS_FILTER_0016) {
                PREVIOUS_FILTER_0016 = filter0016;
                PORTA = (PORTA & ~(1 << PCINT0)) |
                        (1 << PCINT1) | (1 << PCINT2) | (1 << PCINT3);
                writeFilterValue(filter0016);
        }
        if (filter0270 != PREVIOUS_FILTER_0270) {
                PREVIOUS_FILTER_0270 = filter0270;
                PORTA = (PORTA & ~(1 << PCINT1)) |
                        (1 << PCINT0) | (1 << PCINT2) | (1 << PCINT3);
                writeFilterValue(filter0270);
        }
        if (filter5300 != PREVIOUS_FILTER_5300) {
                PREVIOUS_FILTER_5300 = filter5300;
                PORTA = (PORTA & ~(1 << PCINT2)) |
                        (1 << PCINT0) | (1 << PCINT1) | (1 << PCINT3);
                writeFilterValue(filter5300);
        }
        if (filter0000 != PREVIOUS_FILTER_0000) {
                PREVIOUS_FILTER_0000 = filter0000;
                PORTA = (PORTA & ~(1 << PCINT3)) |
                        (1 << PCINT0) | (1 << PCINT1) | (1 << PCINT2);
                writeFilterValue(filter0000);
        }

        // Set all pins to non-active.
        PORTA |= (1 << PCINT0) | (1 << PCINT1) | (1 << PCINT2) | (1 << PCINT3);
}

void enableAllDevices() {
        // For each device, select and then write the value over SPI.
        // Note that the active pin is LOW, not HIGH.
        // Pin 13.
        PORTA = (PORTA & ~(1 << PCINT0)) |
                (1 << PCINT1) | (1 << PCINT2) | (1 << PCINT3);
        writeDisableWriteProtect();
        // Pin 12.
        PORTA = (PORTA & ~(1 << PCINT1)) |
                (1 << PCINT0) | (1 << PCINT2) | (1 << PCINT3);
        writeDisableWriteProtect();
        // Pin 11.
        PORTA = (PORTA & ~(1 << PCINT2)) |
                (1 << PCINT0) | (1 << PCINT1) | (1 << PCINT3);
        writeDisableWriteProtect();
        // Pin 10.
        PORTA = (PORTA & ~(1 << PCINT3)) |
                (1 << PCINT0) | (1 << PCINT1) | (1 << PCINT2);
        writeDisableWriteProtect();

        // Set all pins to non-active.
        PORTA |= (1 << PCINT0) | (1 << PCINT1) | (1 << PCINT2) | (1 << PCINT3);
}

/**
 * Disable write protection on the potentiometers.
 */
void writeDisableWriteProtect() {
        // Write 1 => C1 (write protection bit).
        // Command: 00|0110|00 - 0000|00(C1)0
        //  C0 - 20-TP program enable.
        //  C1 - write protection.
        //  C2 - calibration enable.
        //  C3 - TP-20 program success.
        // so, everything else should be 0.
        writeSPIValue((1 << 4) | (1 << 3));
        writeSPIValue((1 << 1));
}

void writeFilterValue(int value) {
        // Write command: 00|0001|DD - Dx8
        // Send the first byte, a write command and top two data bits.
        writeSPIValue((1 << 3) | (value >> 8));

        // Send the second byte, simply the last 8 data bits.
        writeSPIValue(value & 255);
}

void writeSPIValue(char byte) {
        char i;
        // Load up the byte to write.
        USIDR = byte;

        for(i = 0; i < 8; i++) {
                // Rising clock edge.
                PORTA |= (1 << PCINT4); // USCK/SCL
                // Shift out a bit.
                USICR |= (1 << USICLK);
                // Falling clock edge: the value will get read here.
                PORTA &= ~(1 << PCINT4); // USCK/SCL
        }
}

/**
 * Sleep after writing to the potentiometers.
 */
void sleepForABit() {
        // Usen the 8 bit timer.
        // Initialize the timer register.
        TCNT0 = 0;
        
        // Disconnect the timer output pins and use CTC mode.
        TCCR0A |= (1 << WGM01);
        
        // Compare the timer value against the largest 8-bit value.
        OCR0A = 255;
        
        // Trigger an alert when we match OCR0A.
        TIMSK0 |= (1 << OCIE0A);
        
        // With a 64x prescale, 255*64 is 16ms/64Hz maximum update.
        // This also starts the timer.
        TCCR0B |= (1 << CS01) | (1 << CS00);
                                
        // Keep peripherals (like the timer) running while sleeping.
        set_sleep_mode(SLEEP_MODE_IDLE);
        // Sleep until the timer triggers.
        sleep_mode();
}

/**
 * Handle TP-20 writes requests to the digital potentiometer (AD5292).
 *
 * TP-20 is the on-boot memory of the digital potentiometers: letting
 * all the potentiometers start at the middle of their ranges probably
 * produces weird results. Instead, we can write a value to
 * non-volatile memory that the potentiometer will remember while
 * powered down, and boot with that value. This burn is only possible
 * 20 times, which is why it's called TP-20.
 */

void handleTP20Request() {
        // TODO: implement TP20 functionality if necessary.
}

// Global TP-20 request bit.
char GlobalTP20Setting = 0;

// Out of an abundance of caution, only write once per power cycle. It
// sure would be a shame if I burned all 20 writes in less than a
// second due to a mistake in wiring/coding.
char wroteTP20 = 0;

/**
 * Global state machine
 */
typedef enum {
        SleepingState = 0,
        WaitingForReadState,
        WriteValueState
} State;

State GlobalState;
int ADCValue;
int PreviousADCValue =  0;

void main() {
        /* -- Initial Configuration ----------------------------------------- */
        // By default, the internal 8MHz oscillator is used, and the
        // clock prescaler runs at 1/8 f_clk.
        
        // Set up the ADC for the color pin.
        // With 1Mhz default internal clock, 32x prescale gives the ADC a 30kHz
        // clock (50-200kHz needed for 10 bit resolution).
        // By default, the ADC7 pin is configured as input.
        ADCSRA |=
                (1 << ADEN) | // Enable the ADC.
                (1 << ADIE) | // Enable ADC complete interrupts.
                (1 << ADPS2) | (1 << ADPS0); // Set the ADC prescaler to 32x.
        ADMUX |=
                (1 << REFS0) | // Use Vcc as the reference.
                (1 << MUX2) | (1 << MUX1) | (1 << MUX0); // Select ADC7.
        
        // Set up the SPI communications channels.
        // Set the direction for the chip select pins (PA0/PA1/PA2/PA3 for
        // 16,270,5300,inft respectively).
        DDRA |= (1 << PA0) | (1 << PA1) | (1 << PA2) | (1 << PA3);
        // Set the direction for the SPI pins SCL and MOSI (MISO is default input).
        DDRB |= (1 << PCINT4 /* USCK/SCL */ ) | (1 << PCINT6 /* MOSI */);

        // Configure the SPI device.
        USICR |=
                (0 << USIWM1) | (1 << USIWM0) // Use 3-wire (SPI) mode.
                // Don't use the USIOIE (overflow interrupt) in favor of
                // software strobe.
                // USICSx are 0 for software clock; move the register with USICLK.
                ;

        // Configure each pot to not be read-only.
        enableAllDevices();


        /* -- Main Loop ----------------------------------------------------- */
        while(1) {
                if(GlobalTP20Setting && wroteTP20 == 0) {
                        handleTP20Request();
                        GlobalTP20Setting = 0;
                        wroteTP20 = 1;
                } else {
                        switch(GlobalState) {
                        case SleepingState:
                                // Start a read from the ADC.
                                ADCSRA |= (1 << ADSC);
                                GlobalState = WaitingForReadState;

                                // Sleep until the ADC value is ready.
                                // Keep peripherals running.
                                set_sleep_mode(SLEEP_MODE_IDLE);
                                // Sleep until the ADC is done.
                                sleep_mode();
                        case WaitingForReadState:
                                // Read from the ADC, and write to the
                                // potentiometers.
                                ADCValue = (ADCH << 8) | ADCL;

                                GlobalState = WriteValueState;

                                // Write to the digital potentiometers. Skip
                                // the write if the input value didn't change.
                                if(PreviousADCValue != ADCValue) {
                                        calculateAndWritePotentiometers(ADCValue);
                                }
                                PreviousADCValue = ADCValue;
                                
                                // Go to sleep for a while.
                                GlobalState = SleepingState;
                                sleepForABit();
                        }
                }
        }
}

// Handle the ADC conversion finishing.
ISR(ADC_vect) {
        GlobalState = WriteValueState;
}

// Handle the timer triggering.
ISR(TIM0_COMPA_vect) {
        // Wipe the prescale settings to stop the timer.
        TCCR0B &= ~((1 << CS02) | (1 << CS01) | (1 << CS00));
}

/**
 * Register an interrupt for the button press.
 *
 * This does not do the TP-20 set: instead, this just sets a bit, and
 * when the main loop is finished with its work, it will handle the
 * TP-20 communications necessary to burn in the current values.
 */

/*
// TODO
ISR()
void burnPotentiometers() {
        globalTP20Setting = 1;
}
*/