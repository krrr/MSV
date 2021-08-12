#pragma once


namespace Protect {
	NTSTATUS Initialize();
	void Finalize();
	OB_PREOP_CALLBACK_STATUS PreProcessHandle(
		_In_ PVOID RegistrationContext,
		_Inout_ POB_PRE_OPERATION_INFORMATION OperationInformation
	);
};