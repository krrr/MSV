#include "stdafx.h"
#include "Protect.h"


extern "C" UCHAR *PsGetProcessImageFileName(__in PEPROCESS Process);


#define PROCESS_CREATE_THREAD  (0x0002)
#define PROCESS_VM_OPERATION   (0x0008)  
#define PROCESS_VM_READ        (0x0010)  
#define PROCESS_VM_WRITE       (0x0020)  




namespace Protect {
	PVOID registrationHandle;

	NTSTATUS Initialize() {
		OB_OPERATION_REGISTRATION oor;
		oor.ObjectType = PsProcessType;
		oor.Operations = OB_OPERATION_HANDLE_CREATE | OB_OPERATION_HANDLE_DUPLICATE;
		oor.PreOperation = PreProcessHandle;
		oor.PostOperation = NULL;

		OB_CALLBACK_REGISTRATION ob;
		ob.Version = ObGetFilterVersion();
		ob.OperationRegistrationCount = 1;
		RtlInitUnicodeString(&ob.Altitude, L"1000");
		ob.RegistrationContext = NULL;
		ob.OperationRegistration = &oor;

		return ObRegisterCallbacks(&ob, &registrationHandle);
	}


	void Finalize() {
		if (registrationHandle) {
			ObUnRegisterCallbacks(registrationHandle);
			registrationHandle = nullptr;
		}
	}


	OB_PREOP_CALLBACK_STATUS PreProcessHandle(
		_In_ PVOID RegistrationContext,
		_Inout_ POB_PRE_OPERATION_INFORMATION OperationInformation
	) {
		UNREFERENCED_PARAMETER(RegistrationContext);
		auto source = PsGetCurrentProcess();
		auto srcImageName = PsGetProcessImageFileName(source);  // max 14 characters
		if (_stricmp((const char*)srcImageName, "BlackCipher.ae") != 0) {
			return OB_PREOP_SUCCESS;
		}


		if (OperationInformation->KernelHandle) {  // call made inside of the kernel
			return OB_PREOP_SUCCESS;
		}

		HANDLE pid;
		if (OperationInformation->ObjectType == *PsProcessType) {
			pid = PsGetProcessId((PEPROCESS) OperationInformation->Object);
		} else if (OperationInformation->ObjectType == *PsThreadType) {
			pid = PsGetThreadProcessId((PETHREAD) OperationInformation->Object);
		} else {
			KdPrint(("unknown object type"));
			return OB_PREOP_SUCCESS;
		}

		auto imageName = PsGetProcessImageFileName((PEPROCESS) OperationInformation->Object);
		if (_stricmp((const char*)imageName, "ka.exe") != 0 && _stricmp((const char*)imageName, "msv.exe") != 0) {
			return OB_PREOP_SUCCESS;
		}

		
		ACCESS_MASK bits = PROCESS_CREATE_THREAD | PROCESS_VM_OPERATION | PROCESS_VM_READ | PROCESS_VM_WRITE;
		if (OperationInformation->Parameters->CreateHandleInformation.OriginalDesiredAccess & bits) {
			KdPrint(("MSVDriver: OpenProcess suspicious privilige detected"));
			
		} else {
			KdPrint(("MSVDriver: OpenProcess detected"));
		}
		OperationInformation->Parameters->CreateHandleInformation.DesiredAccess &= 0;

		return OB_PREOP_SUCCESS;
	}
}