import serial

class serialUploader:
    # a class that can be used similarly to the AutoUploader class, but
    # instead of uploading using mouse/keyboard predetermined commands
    # with the Smart Robot Edit software, it uploads the commands directly
    # over the RS 232 port.


    COM_PORT = "COM7"  # COM port to write commands to


    def __init__(self):
        pass


    def setCommands(fisnar_commands):
        pass


    def clearFisnar():
        pass


    @staticmethod
    def getSinglePrecisionBits(number):
        # given a floating point number, return a bit string representing how
        # the number would be stored as a single precision floating point number
        # in accordance with IEEE 754

        def floatToBinary(num, places):
            # helper function for turning a float into its equivalent binary representation

            whole, dec = str(num).split(".")  # splitting into whole number and fraction
            ret_str = bin(int(whole))[2:] + "."  # first part of return string is the whole number in 'traditional' binary

            # getting decimal part
            dec = float("." + dec)
            for i in range(1, places + 1):
                if dec >= 2**(-i):  # 'i'th digit is a 1
                    ret_str += "1"
                    dec = dec - 2**(-i)
                else:  # 'i'th digit is a 0
                    ret_str += "0"

            return ret_str

        # getting sign of number
        sign_bit = 0
        if number < 0:
            sign_bit = 1
            number *= -1
        sign_bit = str(sign_bit)  # for returning binary string later

        # turning decimal number to binary number (with 30 binary 'decimal' places (30 digits after the '.'))
        bin_str = floatToBinary(number, 30)

        # getting indices of the first '1' and the '.' in the binary representation
        first_one_ind = bin_str.find("1")
        dot_ind = bin_str.find(".")

        # preparing the 'to-be' mantissa binary string by removing '.'
        if first_one_ind < dot_ind:
            bin_str = bin_str.replace(".", "")
            dot_ind -= 1
        else:
            bin_str = bin_str.replace(".", "")
            dot_ind -= 1
            first_one_ind -= 1

        # calculating stored exponent and converting to binary
        real_exp = dot_ind - first_one_ind
        stored_exp = real_exp + 127
        exp_bits = bin(stored_exp)[2:].zfill(8)

        # getting stored mantissa from number's binary representation
        mantissa_bits = bin_str[first_one_ind + 1:][:23].ljust(23, "0")
        print(mantissa_bits, len(mantissa_bits))

        # putting it all together
        ret_bits = sign_bit + exp_bits + mantissa_bits
        return(ret_bits)
