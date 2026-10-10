// New project-only resources. No subscription roles, peering or existing account mutations.
targetScope = 'resourceGroup'
param location string = resourceGroup().location
@description('Globally unique name for NEW ciphertext-only storage, not the owner data account.')
param ciphertextStorageName string
param workerName string = 'nftpz-fhe-worker'
@description('Dedicated operator public SSH key; no password auth or public IP is provisioned.')
param operatorSshPublicKey string
param vmSize string = 'Standard_D4s_v5'
param operatorUsername string = 'nftpzoperator'

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${workerName}-identity'
  location: location
}
resource network 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: '${workerName}-vnet'
  location: location
  properties: {
    addressSpace: { addressPrefixes: ['10.87.0.0/16'] }
    subnets: [
      { name: 'worker', properties: { addressPrefix: '10.87.1.0/24', networkSecurityGroup: { id: nsg.id } } }
      { name: 'endpoints', properties: { addressPrefix: '10.87.2.0/24', privateEndpointNetworkPolicies: 'Disabled' } }
    ]
  }
}
resource nsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: '${workerName}-nsg'
  location: location
  properties: {
    securityRules: [
      { name: 'deny-inbound', properties: { priority: 100, direction: 'Inbound', access: 'Deny', protocol: '*', sourcePortRange: '*', destinationPortRange: '*', sourceAddressPrefix: '*', destinationAddressPrefix: '*' } }
      { name: 'blob-endpoint-only', properties: { priority: 100, direction: 'Outbound', access: 'Allow', protocol: 'Tcp', sourcePortRange: '*', destinationPortRange: '443', sourceAddressPrefix: '*', destinationAddressPrefix: '10.87.2.0/24' } }
      { name: 'platform-dns', properties: { priority: 110, direction: 'Outbound', access: 'Allow', protocol: '*', sourcePortRange: '*', destinationPortRange: '53', sourceAddressPrefix: '*', destinationAddressPrefix: 'AzurePlatformDNS' } }
      { name: 'deny-other-outbound', properties: { priority: 4000, direction: 'Outbound', access: 'Deny', protocol: '*', sourcePortRange: '*', destinationPortRange: '*', sourceAddressPrefix: '*', destinationAddressPrefix: '*' } }
    ]
  }
}
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: ciphertextStorageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Disabled'
  }
}
resource blob 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: { deleteRetentionPolicy: { enabled: true, days: 7 } }
}
resource jobs 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blob
  name: 'ciphertext-jobs'
  properties: { publicAccess: 'None' }
}
resource results 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blob
  name: 'ciphertext-results'
  properties: { publicAccess: 'None' }
}
resource jobsReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(jobs.id, identity.id, 'reader')
  scope: jobs
  properties: { principalId: identity.properties.principalId, principalType: 'ServicePrincipal', roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1') }
}
resource resultsWriter 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(results.id, identity.id, 'writer')
  scope: results
  properties: { principalId: identity.properties.principalId, principalType: 'ServicePrincipal', roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') }
}
resource endpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: '${workerName}-blob-endpoint'
  location: location
  properties: {
    subnet: { id: '${network.id}/subnets/endpoints' }
    privateLinkServiceConnections: [{ name: 'blob', properties: { privateLinkServiceId: storage.id, groupIds: ['blob'] } }]
  }
}
resource zone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.blob.${environment().suffixes.storage}'
  location: 'global'
}
resource zoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: zone
  name: '${workerName}-link'
  location: 'global'
  properties: { registrationEnabled: false, virtualNetwork: { id: network.id } }
}
resource dns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: endpoint
  name: 'default'
  properties: { privateDnsZoneConfigs: [{ name: 'blob', properties: { privateDnsZoneId: zone.id } }] }
}
resource nic 'Microsoft.Network/networkInterfaces@2023-11-01' = {
  name: '${workerName}-nic'
  location: location
  properties: { ipConfigurations: [{ name: 'private', properties: { privateIPAllocationMethod: 'Dynamic', subnet: { id: '${network.id}/subnets/worker' } } }] }
}
resource vm 'Microsoft.Compute/virtualMachines@2024-03-01' = {
  name: workerName
  location: location
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${identity.id}': {} } }
  properties: {
    hardwareProfile: { vmSize: vmSize }
    storageProfile: {
      imageReference: { publisher: 'Canonical', offer: 'ubuntu-24_04-lts', sku: 'server', version: 'latest' }
      osDisk: { createOption: 'FromImage', managedDisk: { storageAccountType: 'StandardSSD_LRS' }, diskSizeGB: 64 }
    }
    osProfile: {
      computerName: workerName
      adminUsername: operatorUsername
      linuxConfiguration: { disablePasswordAuthentication: true, ssh: { publicKeys: [{ path: '/home/${operatorUsername}/.ssh/authorized_keys', keyData: operatorSshPublicKey }] } }
    }
    networkProfile: { networkInterfaces: [{ id: nic.id }] }
  }
}
output workerIdentityClientId string = identity.properties.clientId
output vmResourceId string = vm.id
output ciphertextAccount string = storage.name
