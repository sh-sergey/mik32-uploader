
import time
from tclrpc import TclException
from tclrpc import OpenOcdTclRpc

# --------------------------
# PM register offset
# --------------------------
PM_BASE_ADDRESS = 0x000050000

PM_Clk_AHB_Set_OFFSET = 0x0C
PM_Clk_APB_M_Set_OFFSET = 0x14
PM_Clk_APB_P_Set_OFFSET = 0x1C

# --------------------------
# PM register fields
# --------------------------
# AHB BUS
PM_CLOCK_CPU_S = 0
PM_CLOCK_CPU_M = (1 << PM_CLOCK_CPU_S)
PM_CLOCK_EEPROM_S = 1
PM_CLOCK_EEPROM_M  = (1 << PM_CLOCK_EEPROM_S)
PM_CLOCK_RAM_S = 2
PM_CLOCK_RAM_M = (1 << PM_CLOCK_RAM_S)
PM_CLOCK_SPIFI_S = 3
PM_CLOCK_SPIFI_M = (1 << PM_CLOCK_SPIFI_S)
PM_CLOCK_TCB_S = 4
PM_CLOCK_TCB_M = (1 << PM_CLOCK_TCB_S)
PM_CLOCK_DMA_S = 5
PM_CLOCK_DMA_M = (1 << PM_CLOCK_DMA_S)
PM_CLOCK_CRYPTO_S = 6
PM_CLOCK_CRYPTO_M = (1 << PM_CLOCK_CRYPTO_S)
PM_CLOCK_CRC32_S = 7
PM_CLOCK_CRC32_M = (1 << PM_CLOCK_CRC32_S)

# APB M
PM_CLOCK_PM_S = 0
PM_CLOCK_PM_M = (1 << PM_CLOCK_PM_S)

# --------------------------
# WU register offset
# --------------------------
WU_BASE_ADDRESS = 0x00060000

WU_Clocks_OFFSET = 0x10

# --------------------------
# EEPROM register offset
# --------------------------
EEPROM_REGS_BASE_ADDRESS = 0x00070400

EEPROM_REGS_EEDAT = EEPROM_REGS_BASE_ADDRESS + 0x00
EEPROM_REGS_EEA = EEPROM_REGS_BASE_ADDRESS + 0x04
EEPROM_REGS_EECON = EEPROM_REGS_BASE_ADDRESS + 0x08
EEPROM_REGS_EESTA = EEPROM_REGS_BASE_ADDRESS + 0x0C
EEPROM_REGS_EERB = EEPROM_REGS_BASE_ADDRESS + 0x10
EEPROM_REGS_EEADJ = EEPROM_REGS_BASE_ADDRESS + 0x14
EEPROM_REGS_NCYCRL = EEPROM_REGS_BASE_ADDRESS + 0x18
EEPROM_REGS_NCYCEP1 = EEPROM_REGS_BASE_ADDRESS + 0x1C
EEPROM_REGS_NCYCEP2 = EEPROM_REGS_BASE_ADDRESS + 0x20

# --------------------------
# EEPROM register fields
# --------------------------
# EECON
EEPROM_EX_S = 0
EEPROM_OP_S = 1
EEPROM_WRBEH_S = 3
EEPROM_APBNWS_S = 5
EEPROM_DISECC_S = 6
EEPROM_BWE_S = 7
EEPROM_IESERR_S = 8
# EESTA
EEPROM_BSY_S = 0
EEPROM_SERR_S = 1
# NCYCRL
EEPROM_N_LD_S = 0
EEPROM_N_R_1_S = 8
EEPROM_N_R_2_S = 16
# --------------------------
# EEPROM codes
# --------------------------
EEPROM_OP_RD = 0
EEPROM_OP_ER = 1
EEPROM_OP_PR = 2
EEPROM_BEH_EVEN = 1
EEPROM_BEH_ODD = 2
EEPROM_BEH_GLOB = 3

EEPROM_PAGE_MASK = 0x1F80

def eeprom_sysinit(openocd: OpenOcdTclRpc):
    print("MCU clock init...")

    openocd.write_word(WU_BASE_ADDRESS + WU_Clocks_OFFSET, 0x202)
    openocd.write_word(PM_BASE_ADDRESS + PM_Clk_APB_P_Set_OFFSET, 0xffffffff)
    openocd.write_word(PM_BASE_ADDRESS + PM_Clk_APB_M_Set_OFFSET, 0xffffffff)
    openocd.write_word(PM_BASE_ADDRESS + PM_Clk_AHB_Set_OFFSET, 0xffffffff)


def eeprom_global_erase(openocd: OpenOcdTclRpc):
    print("EEPROM global erase...")
    with OpenOcdTclRpc() as openocd:
        openocd.write_word(EEPROM_REGS_NCYCRL, 1 << EEPROM_N_LD_S |
                           3 << EEPROM_N_R_1_S | 1 << EEPROM_N_R_2_S)
        openocd.write_word(EEPROM_REGS_NCYCEP1, 100000)
        openocd.write_word(EEPROM_REGS_NCYCEP2, 1000)
        time.sleep(0.1)
        openocd.write_word(EEPROM_REGS_EECON, (1 << EEPROM_BWE_S)
                           | (EEPROM_BEH_GLOB << EEPROM_WRBEH_S))
        openocd.write_word(EEPROM_REGS_EEA, 0x00000000)
        # buffer load
        for i in range(0, 32):
            openocd.write_word(EEPROM_REGS_EEDAT, 0x00000000)
        # start operation
        openocd.write_word(EEPROM_REGS_EECON, (
            (1 << EEPROM_EX_S) | (1 << EEPROM_BWE_S) |
            (EEPROM_OP_ER << EEPROM_OP_S) | (EEPROM_BEH_GLOB << EEPROM_WRBEH_S)
        ))

def eeprom_global_erase_check(openocd: OpenOcdTclRpc):
    print("EEPROM global erase check through APB...")
    print("  Read Data at ...")
    ex_value = 0x00000000
    openocd.write_word(EEPROM_REGS_EEA, 0x00000000)
    for i in range(0, 64):
        print(f"    Row={i+1}/64")
        for j in range(0, 32):
            value = openocd.read_memory(EEPROM_REGS_EEDAT, 32, 1)[0]
            if ex_value != value:
                print(f"Unexpect value at Row {i}, Word {j}, expect {ex_value:#0x}, {value:#0x}")


def eeprom_write_word(openocd: OpenOcdTclRpc, address:int, word:int):
    openocd.write_word(EEPROM_REGS_EECON, 1 << EEPROM_BWE_S)
    openocd.write_word(EEPROM_REGS_EEA, address)
    # buffer load
    openocd.write_word(EEPROM_REGS_EEDAT, word)
    openocd.write_word(EEPROM_REGS_EECON, (1 << EEPROM_EX_S) | (1 << EEPROM_BWE_S) | (EEPROM_OP_PR << EEPROM_OP_S))
    time.sleep(0.001)

def eeprom_write_page(openocd: OpenOcdTclRpc, address:int, data:list[int]):
    openocd.write_word(EEPROM_REGS_EECON, 1 << EEPROM_BWE_S)
    openocd.write_word(EEPROM_REGS_EEA, address)
    page_address = address & EEPROM_PAGE_MASK
    n = 0
    # buffer load
    for word in data:
        if ((address + n) & EEPROM_PAGE_MASK) != page_address:
            raise Exception("ERROR: word outside page!")
        openocd.write_word(EEPROM_REGS_EEDAT, word)
    openocd.write_word(EEPROM_REGS_EECON, (1 << EEPROM_EX_S) | (1 << EEPROM_BWE_S) | (EEPROM_OP_PR << EEPROM_OP_S))
    time.sleep(0.001)

def eeprom_check_data_apb(openocd: OpenOcdTclRpc, words: list[int]):
    print("EEPROM check through APB...")
    openocd.write_word(EEPROM_REGS_EEA, 0x00000000)
    word_num = 0
    progress = 0
    print("[", end="", flush=True)
    for word in words:
        value:int = openocd.read_word(EEPROM_REGS_EEDAT)
        if words[word_num] != value:
            print(f"Unexpect value at {word_num} word, expect {word:#0x}, get {value:#0x}")
        word_num += 1
        curr_progress = int((word_num * 50) / len(words))
        if curr_progress > progress:
            print("#"*(curr_progress - progress), end="", flush=True)
            progress = curr_progress
    print("]")
    print("EEPROM check through APB done!")

def eeprom_check_data_ahb_lite(openocd: OpenOcdTclRpc, words: list[int]):
    print("EEPROM check through AHB-Lite...")
    mem_array = openocd.read_memory(0x01000000, 32, len(words))
    if len(words) != len(mem_array):
        raise Exception("Wrong number of words in read_memory output!")
    progress = 0
    print("[", end="", flush=True)
    for word_num in range(len(words)):
        if words[word_num] != mem_array[word_num]:
            print(f"Unexpect value at {word_num} word, expect {words[word_num]:#0x}, \
            get {mem_array[word_num]:#0x}")
        curr_progress = int((word_num * 50) / len(words))
        if curr_progress > progress:
            print("#"*(curr_progress - progress), end="", flush=True)
            progress = curr_progress
    print("]")
    print("EEPROM check through APB done!")


def write_words(words: list[int], write_by_word = False, read_through_apb = False):
    """
    Write words in MIK32 EEPROM through APB bus

    @words: list of words to write at offset 0x0
    @write_by_word: if True, write every word in separete page flash operation
    @read_through_apb: if True, check written words through APB instead of AHB-Lite

    TODO: implement setting byte array offset, add error handling, 
    improve progress visualisation, add option check page immidiately after writing
    """
    print(f"Write {len(words*4)} bytes")
    with OpenOcdTclRpc() as openocd:
        openocd.halt()
        eeprom_sysinit(openocd)
        eeprom_global_erase(openocd)
        # eeprom_global_erase_check(openocd)
        openocd.write_word(EEPROM_REGS_NCYCRL, 1<<EEPROM_N_LD_S  | 3<<EEPROM_N_R_1_S | 1<<EEPROM_N_R_2_S)
        openocd.write_word(EEPROM_REGS_NCYCEP1, 100000)
        openocd.write_word(EEPROM_REGS_NCYCEP2, 1000)
        time.sleep(0.1)
        word_num:int = 0
        progress:int = 0
        print("EEPROM writing...")
        print("[", end="", flush=True)
        if write_by_word:
            for word in words:
                eeprom_write_word(openocd, word_num*4, word)
                word_num += 1
                curr_progress = int((word_num * 50) / len(words))
                if curr_progress > progress:
                    print("#"*(curr_progress - progress), end="", flush=True)
                    progress = curr_progress
        else:
            page = []
            page_num = 0
            page_size = 32
            while word_num < len(words):
                if word_num < page_size*(page_num+1):
                    page.append(words[word_num])
                    word_num += 1
                else:
                    # print(list(map(lambda word: f"{word:#0x}", page)))
                    eeprom_write_page(openocd, page_num*page_size*4, page)
                    page_num += 1
                    page.clear()
                curr_progress = int((word_num * 50) / len(words))
                if curr_progress > progress:
                    print("#"*(curr_progress - progress), end="", flush=True)
                    progress = curr_progress
            eeprom_write_page(openocd, page_num*page_size*4, page)
        print("]")
        if read_through_apb:
            eeprom_check_data_apb(openocd, words)
        else:
            eeprom_check_data_ahb_lite(openocd, words)
        openocd.resume(0)
    print("EEPROM write file done!")
