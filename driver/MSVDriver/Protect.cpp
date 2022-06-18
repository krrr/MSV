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
		OB_OPERATION_REGISTRATION oor[2];
		oor[0].ObjectType = PsProcessType;
		oor[0].Operations = OB_OPERATION_HANDLE_CREATE | OB_OPERATION_HANDLE_DUPLICATE;
		oor[0].PreOperation = PreProcessHandle;
		oor[0].PostOperation = NULL;
		oor[1].ObjectType = PsThreadType;
		oor[1].Operations = OB_OPERATION_HANDLE_CREATE | OB_OPERATION_HANDLE_DUPLICATE;
		oor[1].PreOperation = PreProcessHandle;
		oor[1].PostOperation = NULL;

		OB_CALLBACK_REGISTRATION ob;
		ob.Version = OB_FLT_REGISTRATION_VERSION;
		ob.OperationRegistrationCount = ARRAYSIZE(oor);
		RtlInitUnicodeString(&ob.Altitude, L"1000");
		ob.RegistrationContext = NULL;
		ob.OperationRegistration = oor;

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

		if (OperationInformation->KernelHandle) {  // call made inside of the kernel
			return OB_PREOP_SUCCESS;
		}

		auto source = PsGetCurrentProcess();
		auto srcImageName = PsGetProcessImageFileName(source);  // max 14 characters
		if (_stricmp((const char*)srcImageName, "BlackCipher.ae") != 0) {
			return OB_PREOP_SUCCESS;
		}

		HANDLE pid;
		PEPROCESS target_proc;
		if (OperationInformation->ObjectType == *PsProcessType) {
			target_proc = (PEPROCESS)OperationInformation->Object;
			pid = PsGetProcessId(target_proc);
		} else {  // PsThreadType
			pid = PsGetThreadProcessId((PETHREAD) OperationInformation->Object);
			if (!NT_SUCCESS(PsLookupProcessByProcessId(pid, &target_proc))) {
				KdPrint(("PsLookupProcessByProcessId failed"));
				return OB_PREOP_SUCCESS;
			}
		}

		auto imageName = PsGetProcessImageFileName(target_proc);
		if (_stricmp((const char*)imageName, "ka.exe") != 0 && _stricmp((const char*)imageName, "msv.exe") != 0) {
			return OB_PREOP_SUCCESS;
		}

		if (OperationInformation->ObjectType == *PsProcessType) {
			ACCESS_MASK bits = PROCESS_CREATE_THREAD | PROCESS_VM_OPERATION | PROCESS_VM_READ | PROCESS_VM_WRITE;
			if (OperationInformation->Parameters->CreateHandleInformation.OriginalDesiredAccess & bits) {
				KdPrint(("MSVDriver: OpenProcess suspicious privilige detected"));
			}
			else {
				KdPrint(("MSVDriver: OpenProcess detected"));
			}
		} else {  // PsThreadType
			KdPrint(("MSVDriver: OpenThread detected"));
		}
		OperationInformation->Parameters->CreateHandleInformation.DesiredAccess &= 0;

		return OB_PREOP_SUCCESS;
	}
}