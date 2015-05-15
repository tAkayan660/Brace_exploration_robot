import webiopi
import subprocess
import datetime
from webiopi import deviceInstance
from webiopi.devices.analog.mcp3x0x import MCP3X0X

class MCP3002(MCP3X0X):
	def __init__(self, chip, channelCount, name):
		MCP3X0X.__init__(self, chip, channelCount, 10, name)

	def __command__(self, channel, diff):
		d = [0x00, 0x00]
		d[0] |= 1 << 6					# start
		d[0] |= (not diff) << 5			# SGL
		d[0] |= (channel & 0x01) << 4	# Ch
		d[0] |= (1) << 3				# MBSF
		return d

	def __analogRead__(self, channel, diff):
		data = self.__command__(channel, diff)
		r = self.xfer(data)
		return ((r[0] & self.MSB_MASK) << 8) | r[1]

GPIO = webiopi.GPIO
pwm0 = deviceInstance("pwm0")

PIN_L1 = 6
PIN_L2 = 5
PIN_R1 = 13
PIN_R2 = 19
PIN_SUB1 = 20
PIN_SUB2 = 21

Foot = 0
ServoTop = 0
ServoLower = -3

g_mode = 0
g_percentage = 50
g_percentageSUB = 100
mcp = MCP3002(0, 2, "MCP3002")

GPIO.setFunction(PIN_L1, GPIO.PWM)
GPIO.setFunction(PIN_L2, GPIO.PWM)
GPIO.setFunction(PIN_R1, GPIO.PWM)
GPIO.setFunction(PIN_R2, GPIO.PWM)
GPIO.setFunction(PIN_SUB1, GPIO.PWM)
GPIO.setFunction(PIN_SUB2, GPIO.PWM)

def setup():
    GPIO.setFunction(25, GPIO.OUT)
    GPIO.output(25, GPIO.HIGH)

def loop():
    GPIO.output(25, not GPIO.input(25))

def MotorDrive(In1, In2, percentage):
	if 100 < percentage:
		percentage = 100
	if percentage < -100:
		percentage = -100
	if -10 < percentage < 10:
		GPIO.pwmWrite(In1, 0)
		GPIO.pwmWrite(In2, 0)
	elif 0 < percentage:
		GPIO.pwmWrite(In1, percentage * 0.01)
		GPIO.pwmWrite(In2, 0)
	else:
		GPIO.pwmWrite(In1, 0)
		GPIO.pwmWrite(In2, -percentage * 0.01)

@webiopi.macro
def ChangeDriveMode(mode):
	if mode == "0":
		MotorDrive(PIN_L1, PIN_L2, 0);
		MotorDrive(PIN_R1, PIN_R2, 0);
	elif mode == "1":
		MotorDrive(PIN_L1, PIN_L2, g_percentage);
		MotorDrive(PIN_R1, PIN_R2, g_percentage);
	elif mode == "2":
		MotorDrive(PIN_L1, PIN_L2, -g_percentage);
		MotorDrive(PIN_R1, PIN_R2, -g_percentage);
	elif mode == "3":
		MotorDrive(PIN_L1, PIN_L2, g_percentage);
		MotorDrive(PIN_R1, PIN_R2, -g_percentage);
	elif mode == "4":
		MotorDrive(PIN_L1, PIN_L2, -g_percentage);
		MotorDrive(PIN_R1, PIN_R2, g_percentage);
	global g_mode
	g_mode = mode

@webiopi.macro
def ChangeVoltageLevel(level):
	global g_percentage
	g_percentage = 10 * int(level)
	ChangeDriveMode(g_mode)

@webiopi.macro
def GetCh1Value():
	return "{}".format(mcp.analogRead(1))

@webiopi.macro
def ChangeModeSUB(modeSUB):
	if modeSUB == "0":
		MotorDrive(PIN_SUB1, PIN_SUB2, 0);
	elif modeSUB == "1":
		MotorDrive(PIN_SUB1, PIN_SUB2, g_percentageSUB);
	elif modeSUB == "2":
		MotorDrive(PIN_SUB1, PIN_SUB2, -g_percentageSUB);

@webiopi.macro
def ChangeForefootBtn(forefoot):
	global Foot
	if forefoot == "0":
		Foot = 0
		pwm0.pwmWriteAngle(0, 0)
		pwm0.pwmWriteAngle(1, 0)
	elif forefoot == "1":
		if Foot <= 60:
			Foot += 20
			pwm0.pwmWriteAngle(0, Foot)
			pwm0.pwmWriteAngle(1, -Foot)
	elif forefoot == "2":
		if Foot <= 120:
			Foot -= 20
			pwm0.pwmWriteAngle(0, Foot)
			pwm0.pwmWriteAngle(1, -Foot)

@webiopi.macro
def ChangeCameraBtn(camera):
	global ServoTop
	global ServoLower
	if camera == "0":
		ServoTop = 0
		ServoLower = -3
		pwm0.pwmWriteAngle(2, ServoTop)
		pwm0.pwmWriteAngle(3, ServoLower)
	elif camera == "1":
		if ServoTop >= -60:
			ServoTop -= 20
			pwm0.pwmWriteAngle(2, ServoTop)
	elif camera == "2":
		if ServoTop <= 40:
			ServoTop += 20
			pwm0.pwmWriteAngle(2, ServoTop)
	elif camera == "3":
		if ServoLower >= -60:
			ServoLower -= 20
			pwm0.pwmWriteAngle(3, ServoLower)
	elif camera == "4":
		if ServoLower <= 60:
			ServoLower += 20
			pwm0.pwmWriteAngle(3, ServoLower)
	elif camera == "5":
		pwm0.pwmWriteAngle(2, -25)
		pwm0.pwmWriteAngle(3, 22)
	elif camera == "6":
		pwm0.pwmWriteAngle(2, -25)
		pwm0.pwmWriteAngle(3, -28)
	elif camera == "7":
		pwm0.pwmWriteAngle(2, 25)
		pwm0.pwmWriteAngle(3, 22)
	elif camera == "8":
		pwm0.pwmWriteAngle(2, 25)
		pwm0.pwmWriteAngle(3, -28)

@webiopi.macro
def ChangeShotBtn(shot):
	if shot == "0":
		time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		subprocess.call([
			"wget", "-O", "/home/pi/Snapshot/{}.jpg".format(time), "http://192.168.0.102:9000/?action=snapshot"
			])